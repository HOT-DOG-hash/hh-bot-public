import asyncio
import logging
from datetime import date
from urllib.parse import parse_qs, urlparse

import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils import buttons, states, texts
from utils.helpers import build_multi_choice_keyboard, build_paginated_keyboard, handle_multi_choice
from utils.states import (
    ASK_COVER_LETTER,
    ASK_EMPLOYMENT,
    ASK_HH_URL,
    ASK_KEYWORD,
    ASK_PROFESSION,
    ASK_REGION,
    ASK_RESUME,
    ASK_SCHEDULE,
    ASK_SEARCH_FIELD,
    ASK_SEARCH_METHOD,
    CONFIRMATION,
    SELECTING_ACTION,
)

from .start import in_development

# Константы
DAILY_RESPONSE_LIMIT = 200


def get_daily_responses_key(user_id: int) -> str:
    """Генерирует ключ для хранения дневных откликов пользователя"""
    today = date.today().isoformat()
    return f"daily_responses_{user_id}_{today}"


def get_daily_response_count(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    """Получает количество откликов пользователя за сегодня"""
    key = get_daily_responses_key(user_id)
    return context.bot_data.get(key, 0)


def increment_daily_response_count(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    """Увеличивает счетчик откликов пользователя за сегодня"""
    key = get_daily_responses_key(user_id)
    current_count = context.bot_data.get(key, 0)
    new_count = current_count + 1
    context.bot_data[key] = new_count
    return new_count


def get_remaining_responses(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    """Получает количество оставшихся откликов на сегодня"""
    used = get_daily_response_count(context, user_id)
    return max(0, DAILY_RESPONSE_LIMIT - used)


async def start_responses_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Создать новый запрос", callback_data="new_request")],
        [InlineKeyboardButton("Выбрать из прошлых запросов", callback_data="past_requests")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(texts.CHOOSE_ACTION, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(texts.CHOOSE_ACTION, reply_markup=reply_markup)

    return SELECTING_ACTION


async def ask_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["new_request"] = {}

    # Используем демо-резюме из конфига
    resumes = config.DEMO_RESUMES

    keyboard = [
        [InlineKeyboardButton(resume["title"], callback_data=f"resume_{resume['id']}")]
        for resume in resumes
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = texts.ASK_RESUME
    await query.message.edit_text(text, reply_markup=reply_markup)
    return ASK_RESUME


async def ask_search_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data["new_request"]["resume"] = query.data.replace("resume_", "")
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Настроить фильтры", callback_data="configure_filters")],
        [InlineKeyboardButton("Вставить ссылку hh.ru", callback_data="paste_link")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("Выберите способ настройки поиска:", reply_markup=reply_markup)
    return ASK_SEARCH_METHOD


async def ask_country_for_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Используем демо-страны из конфига
    countries = config.DEMO_COUNTRIES
    context.bot_data["countries"] = countries

    reply_markup = build_paginated_keyboard(countries, page=0, prefix="country")
    await query.message.edit_text(texts.ASK_COUNTRY, reply_markup=reply_markup)

    return ASK_REGION


async def handle_country_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Парсим данные пагинации
    parts = query.data.split("_")
    if len(parts) >= 4 and parts[1] == "country" and parts[2] == "nav":
        page = int(parts[3])
    else:
        page = int(parts[2])

    countries = context.bot_data["countries"]
    reply_markup = build_paginated_keyboard(countries, page=page, prefix="country")
    await query.edit_message_reply_markup(reply_markup)
    return ASK_REGION


async def ask_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    country_id = query.data.replace("country_", "")
    context.user_data["new_request"]["country"] = country_id
    await query.answer()

    # Используем демо-регионы из конфига
    regions = config.DEMO_REGIONS.get(country_id, [])
    if not any(r["id"] == f"all_{country_id}" for r in regions):
        regions.insert(0, {"id": f"all_{country_id}", "name": "По всей стране"})

    context.bot_data[f"regions_{country_id}"] = regions
    reply_markup = build_paginated_keyboard(regions, page=0, prefix=f"region_{country_id}")
    await query.message.edit_text(texts.ASK_REGION, reply_markup=reply_markup)

    return ASK_SCHEDULE


async def handle_region_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    _, _, country_id, page_str = query.data.split("_")
    page = int(page_str)
    regions = context.bot_data[f"regions_{country_id}"]
    reply_markup = build_paginated_keyboard(regions, page=page, prefix=f"region_{country_id}")
    await query.answer()
    await query.edit_message_reply_markup(reply_markup)
    return ASK_SCHEDULE


async def ask_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data["new_request"]["region"] = query.data.replace("region_", "")
    await query.answer()

    # Используем демо-графики из конфига
    schedules = config.DEMO_SCHEDULES
    context.bot_data["dictionaries"] = {"schedule": schedules}

    schedule_options = {item["id"]: item["name"] for item in schedules}
    context.user_data["schedule_selection"] = set()
    reply_markup = build_multi_choice_keyboard(
        schedule_options, "schedule_selection", "schedule", context
    )
    await query.message.edit_text(texts.ASK_SCHEDULE, reply_markup=reply_markup)
    return ASK_EMPLOYMENT


async def handle_schedule_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    schedules = config.DEMO_SCHEDULES
    schedule_options = {item["id"]: item["name"] for item in schedules}
    await handle_multi_choice(update, context, schedule_options, "schedule_selection", "schedule")
    return ASK_EMPLOYMENT


async def ask_employment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data["new_request"]["schedule"] = list(
        context.user_data.get("schedule_selection", [])
    )
    await query.answer()

    # Используем демо-занятость из конфига
    employment = config.DEMO_EMPLOYMENT
    context.bot_data["dictionaries"]["employment"] = employment

    employment_options = {item["id"]: item["name"] for item in employment}
    context.user_data["employment_selection"] = set()
    reply_markup = build_multi_choice_keyboard(
        employment_options, "employment_selection", "employment", context
    )
    await query.message.edit_text(texts.ASK_EMPLOYMENT, reply_markup=reply_markup)
    return ASK_PROFESSION


async def handle_employment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    employment = config.DEMO_EMPLOYMENT
    employment_options = {item["id"]: item["name"] for item in employment}
    await handle_multi_choice(
        update, context, employment_options, "employment_selection", "employment"
    )
    return ASK_PROFESSION


async def ask_profession(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data["new_request"]["employment"] = list(
        context.user_data.get("employment_selection", [])
    )
    await query.answer()

    # Используем демо-профессии из конфига
    categories = config.DEMO_PROFESSIONS
    context.bot_data["prof_categories"] = categories

    prof_options = {str(cat["id"]): cat["name"] for cat in categories}
    context.bot_data["prof_options"] = prof_options

    context.user_data["profession_selection"] = set()
    reply_markup = build_multi_choice_keyboard(
        prof_options, "profession_selection", "profession", context
    )
    await query.message.edit_text(texts.ASK_PROFESSION, reply_markup=reply_markup)

    return ASK_PROFESSION


async def handle_profession_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prof_options = context.bot_data.get("prof_options", {})
    await handle_multi_choice(update, context, prof_options, "profession_selection", "profession")
    # Сохраняем выбранные проф. области в new_request
    context.user_data["new_request"]["profession"] = list(
        context.user_data.get("profession_selection", [])
    )
    return ASK_PROFESSION


async def ask_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_request"]["profession"] = list(
        context.user_data.get("profession_selection", [])
    )
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(texts.ASK_KEYWORD)
    return ASK_KEYWORD


async def ask_search_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_request"]["keyword"] = update.message.text
    context.user_data["search_field_selection"] = set()

    # Используем новую функцию для текста
    search_field_text = texts.get_search_field_text(update.message.text)
    reply_markup = build_multi_choice_keyboard(
        buttons.SEARCH_FIELD_OPTIONS, "search_field_selection", "search", context
    )
    await update.message.reply_text(search_field_text, reply_markup=reply_markup)
    return ASK_SEARCH_FIELD


async def handle_search_field_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await handle_multi_choice(
        update, context, buttons.SEARCH_FIELD_OPTIONS, "search_field_selection", "search"
    )
    return ASK_SEARCH_FIELD


def get_cover_letter_keyboard(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    cover_letters = context.user_data.get("cover_letters", [])
    keyboard = []

    # Добавляем существующие сопроводительные письма
    if cover_letters:
        for i, letter in enumerate(cover_letters):
            keyboard.append(
                [InlineKeyboardButton(f"📄 {letter['title']}", callback_data=f"cl_select_{i}")]
            )

    # Добавляем опцию создания нового письма
    keyboard.append([InlineKeyboardButton("✏️ Написать новое письмо", callback_data="cl_write_new")])

    # Добавляем опцию без письма
    keyboard.append(
        [InlineKeyboardButton("📭 Без сопроводительного письма", callback_data="no_letter")]
    )

    return InlineKeyboardMarkup(keyboard)


async def ask_cover_letter_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        context.user_data["new_request"]["search_fields"] = list(
            context.user_data.get("search_field_selection", [])
        )
        await query.answer()
        message_to_edit = query.message
    else:
        # This case handles transition from URL paste
        message_to_edit = update.message

    reply_markup = get_cover_letter_keyboard(context)

    await message_to_edit.edit_text(texts.ASK_COVER_LETTER, reply_markup=reply_markup)
    return ASK_COVER_LETTER


async def handle_cover_letter_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Проверяем, ожидаем ли мы новое сопроводительное письмо
    if context.user_data.get("waiting_for_new_cover_letter", False):
        context.user_data["new_request"]["cover_letter"] = update.message.text
        context.user_data.pop("waiting_for_new_cover_letter", None)  # Убираем флаг
        await confirmation(update, context, message=update.message)
        return CONFIRMATION
    else:
        # Если не ожидаем новое письмо, игнорируем сообщение
        return ASK_COVER_LETTER


async def handle_cl_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    letter_index = int(query.data.split("_")[-1])
    letter = context.user_data["cover_letters"][letter_index]
    context.user_data["new_request"]["cover_letter"] = letter["body"]
    await query.answer()
    await confirmation(update, context, message=query.message)
    return CONFIRMATION


async def handle_no_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data["new_request"]["cover_letter"] = "Без сопроводительного письма"
    await query.answer()
    await confirmation(update, context, message=query.message)
    return CONFIRMATION


async def ask_new_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает новое сопроводительное письмо для текущего отклика"""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("Напишите сопроводительное письмо для этого отклика:")
    # Устанавливаем флаг, что ожидаем новое письмо
    context.user_data["waiting_for_new_cover_letter"] = True
    return ASK_COVER_LETTER


async def ask_hh_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks the user to paste a URL from hh.ru."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "Пожалуйста, вставьте ссылку с параметрами поиска из адресной строки hh.ru (демо-режим)."
    )
    return ASK_HH_URL


async def handle_hh_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses the hh.ru URL and moves to the cover letter step."""
    url_text = update.message.text
    try:
        parsed_url = urlparse(url_text)
        query_params = parse_qs(parsed_url.query)

        data = context.user_data["new_request"]
        data["keyword"] = query_params.get("text", [""])[0]
        # В URL параметр area может быть один
        area_list = query_params.get("area", [])
        if area_list:
            data["area"] = area_list

        data["schedule"] = query_params.get("schedule", [])
        data["employment"] = query_params.get("employment", [])
        data["profession"] = query_params.get("professional_role", [])
        data["search_fields"] = query_params.get("search_field", [])
        data["search_by_url"] = True

        logging.info(f"Parsed URL (demo mode). New request data: {data}")

        reply_markup = get_cover_letter_keyboard(context)
        await update.message.reply_text(texts.ASK_COVER_LETTER, reply_markup=reply_markup)

        return ASK_COVER_LETTER

    except Exception as e:
        logging.error(f"Failed to parse HH URL (demo mode): {url_text}. Error: {e}", exc_info=True)
        await update.message.reply_text(
            "Не удалось распознать ссылку. Пожалуйста, убедитесь, что вы скопировали правильную ссылку и попробуйте снова."
        )
        return ASK_HH_URL


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None):
    data = context.user_data["new_request"]

    # Если пришли из URL, показываем упрощенное подтверждение
    if data.get("search_by_url"):
        country_name = "Из ссылки"
        region_name = "Из ссылки"
        schedule_names = data.get("schedule", []) or ["Не указано"]
        employment_names = data.get("employment", []) or ["Не указано"]
        prof_category_names = data.get("profession", []) or ["Не указано"]
        search_field_names = data.get("search_fields", []) or ["Не указано"]
    else:
        # Используем демо-данные
        country_name = next(
            (c["name"] for c in config.DEMO_COUNTRIES if c["id"] == str(data.get("country"))),
            "Не указано",
        )

        region_id_str = data.get("region", "")
        if region_id_str.startswith("all_"):
            region_name = "Вся страна"
        else:
            country_id = data.get("country")
            all_regions = config.DEMO_REGIONS.get(country_id, [])
            region_name = next(
                (r["name"] for r in all_regions if r["id"] == region_id_str), region_id_str
            )

        schedule_names = [
            s["name"] for s in config.DEMO_SCHEDULES if s["id"] in data.get("schedule", [])
        ]
        employment_names = [
            e["name"] for e in config.DEMO_EMPLOYMENT if e["id"] in data.get("employment", [])
        ]

        prof_category_names = [
            c["name"] for c in config.DEMO_PROFESSIONS if str(c["id"]) in data.get("profession", [])
        ]

        search_field_names = [
            buttons.SEARCH_FIELD_OPTIONS.get(f, f) for f in data.get("search_fields", [])
        ]

    cover_letter_text = data.get("cover_letter", "Без сопроводительного письма")

    # Демо-данные для вакансий
    vacancy_count = len(config.DEMO_VACANCIES)
    hh_ru_link = "https://hh.ru/search/vacancy?text=" + data.get("keyword", "demo")

    # Получаем информацию о дневных лимитах
    user_id = update.effective_user.id if update.effective_user else 0
    daily_count = get_daily_response_count(context, user_id)
    remaining_count = get_remaining_responses(context, user_id)

    summary_text = texts.get_confirmation_text(
        vacancy_count=vacancy_count,
        hh_ru_link=hh_ru_link,
        country_name=country_name,
        region_name=region_name,
        schedule=", ".join(schedule_names) or "Не указано",
        employment=", ".join(employment_names) or "Не указано",
        profession=", ".join(prof_category_names) or "Не указано",
        keyword=data.get("keyword", "Не указано"),
        search_field=", ".join(search_field_names) or "Не указано",
        cover_letter=cover_letter_text,
        daily_count=daily_count,
        remaining_count=remaining_count,
    )

    keyboard = [
        [InlineKeyboardButton("Отправить отклики", callback_data="send_responses")],
        [InlineKeyboardButton("Создать новый запрос", callback_data="restart_flow")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if message:
        try:
            await message.edit_text(
                summary_text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            # Если не удается отредактировать сообщение, отправляем новое
            logging.warning(f"Failed to edit message: {e}")
            await message.reply_text(
                summary_text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )


async def send_responses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    # Проверяем дневной лимит
    remaining = get_remaining_responses(context, user_id)
    if remaining <= 0:
        await query.message.edit_text(
            "❌ Достигнут дневной лимит откликов (200/день). Попробуйте завтра."
        )
        return ConversationHandler.END

    # Показываем финальное сообщение
    keyboard = [[InlineKeyboardButton("Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(texts.RESPONSES_STARTED, reply_markup=reply_markup)

    context.user_data.clear()
    return ConversationHandler.END


async def send_test_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет тестовый отклик"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    remaining = get_remaining_responses(context, user_id)
    if remaining <= 0:
        await query.message.edit_text(
            "❌ Достигнут дневной лимит откликов (200/день). Попробуйте завтра."
        )
        return CONFIRMATION

    await query.message.edit_text("🧪 Отправляем тестовый отклик...")

    # Симуляция отправки
    await asyncio.sleep(2)

    # Используем первую демо-вакансию
    vacancy = config.DEMO_VACANCIES[0]

    new_count = increment_daily_response_count(context, user_id)
    remaining = get_remaining_responses(context, user_id)
    result_text = (
        f"✅ Тестовый отклик отправлен!\n\n"
        f"📋 Вакансия: {vacancy.get('name', 'Не указано')}\n"
        f"🏢 Компания: {vacancy.get('employer', {}).get('name', 'Не указано')}\n\n"
        f"📊 Статистика:\n"
        f"Отправлено сегодня: {new_count}/200\n"
        f"Осталось: {remaining}"
    )

    await query.message.edit_text(result_text)

    return CONFIRMATION


def get_responses_conv_handler():
    from routers import menu, start

    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_responses_entry, pattern="^start_responses$"),
            CommandHandler("responses", start_responses_entry),
        ],
        states={
            states.SELECTING_ACTION: [
                CallbackQueryHandler(ask_resume, pattern="^new_request$"),
                CallbackQueryHandler(in_development, pattern="^past_requests$"),
            ],
            states.ASK_RESUME: [CallbackQueryHandler(ask_search_method, pattern="^resume_")],
            states.ASK_SEARCH_METHOD: [
                CallbackQueryHandler(ask_country_for_filters, pattern="^configure_filters$"),
                CallbackQueryHandler(ask_hh_url, pattern="^paste_link$"),
            ],
            states.ASK_HH_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hh_url)],
            states.ASK_COUNTRY: [CallbackQueryHandler(ask_country_for_filters, pattern="^resume_")],
            states.ASK_REGION: [
                CallbackQueryHandler(ask_region, pattern="^country_"),
                CallbackQueryHandler(handle_country_page, pattern="^page_country_nav_"),
            ],
            states.ASK_SCHEDULE: [
                CallbackQueryHandler(ask_schedule, pattern="^region_"),
                CallbackQueryHandler(handle_region_page, pattern=r"^page_region_\d+_\d+$"),
            ],
            states.ASK_EMPLOYMENT: [
                CallbackQueryHandler(handle_schedule_choice, pattern="^schedule_(?!next)"),
                CallbackQueryHandler(ask_employment, pattern="^schedule_next$"),
            ],
            states.ASK_PROFESSION: [
                CallbackQueryHandler(handle_employment_choice, pattern="^employment_(?!next)"),
                CallbackQueryHandler(ask_profession, pattern="^employment_next$"),
                CallbackQueryHandler(handle_profession_choice, pattern="^profession_(?!next)"),
                CallbackQueryHandler(ask_keyword, pattern="^profession_next$"),
            ],
            states.ASK_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_search_field)],
            states.ASK_SEARCH_FIELD: [
                CallbackQueryHandler(handle_search_field_choice, pattern="^search_(?!next)"),
                CallbackQueryHandler(ask_cover_letter_options, pattern="^search_next$"),
            ],
            states.ASK_COVER_LETTER: [
                CallbackQueryHandler(handle_no_cover_letter, pattern="^no_letter$"),
                CallbackQueryHandler(handle_cl_selection, pattern=r"^cl_select_\d+$"),
                CallbackQueryHandler(ask_new_cover_letter, pattern="^cl_write_new$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cover_letter_text),
            ],
            states.CONFIRMATION: [
                CallbackQueryHandler(send_responses, pattern="^send_responses$"),
                CallbackQueryHandler(ask_resume, pattern="^restart_flow$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start.start_over),
            CallbackQueryHandler(menu.back_to_main_menu, pattern="^main_menu$"),
        ],
        allow_reentry=True,
    )
