import logging
from datetime import datetime
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
from utils import texts
from utils.helpers import build_paginated_keyboard
from utils.states import (
    # Импортируем состояния из обычных откликов для переиспользования логики
    AUTO_RESPONSE_CONFIRMATION,
    AUTO_RESPONSE_COVER_LETTER,
    AUTO_RESPONSE_FILTERS,
    AUTO_RESPONSE_HH_URL,
    AUTO_RESPONSE_MAIN,
    AUTO_RESPONSE_RESUME,
    AUTO_RESPONSE_SEARCH_METHOD,
)


async def show_auto_responses_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает главное меню автооткликов"""
    # Проверяем, активны ли автоотклики
    auto_response_active = context.user_data.get("auto_response_active", False)

    if auto_response_active:
        # Показываем статус активных автооткликов
        auto_response_data = context.user_data.get("auto_response_settings", {})
        start_date = auto_response_data.get("start_date", "Не указано")
        start_time = auto_response_data.get("start_time", "Не указано")
        today_count = auto_response_data.get("today_count", 0)
        total_count = auto_response_data.get("total_count", 0)

        # Формируем информацию о фильтрах
        if auto_response_data.get("search_by_url"):
            filters_info = f"Поиск по ссылке: {auto_response_data.get('hh_url', 'Не указано')}"
        else:
            filters_info = "Настроенные фильтры в боте"

        text = texts.get_auto_response_active_status(
            start_date, start_time, today_count, total_count, filters_info
        )

        keyboard = [
            [InlineKeyboardButton("⏹️ Остановить автоотклики", callback_data="auto_stop")],
            [InlineKeyboardButton("⚙️ Изменить параметры", callback_data="auto_change_settings")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
        ]
    else:
        # Показываем приглашение к настройке
        text = texts.AUTO_RESPONSE_MAIN
        keyboard = [
            [InlineKeyboardButton("▶️ Включить автоотклики", callback_data="auto_setup")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

    return AUTO_RESPONSE_MAIN


async def start_auto_response_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает настройку автооткликов"""
    query = update.callback_query
    await query.answer()

    # Инициализируем данные автооткликов
    context.user_data["auto_response_setup"] = {}

    # Переходим к выбору резюме
    return await ask_auto_response_resume(update, context)


async def ask_auto_response_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 1: Выбор резюме для автооткликов"""
    # Используем демо-резюме из конфига
    resumes = config.DEMO_RESUMES

    keyboard = [
        [InlineKeyboardButton(resume["title"], callback_data=f"auto_resume_{resume['id']}")]
        for resume in resumes
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="auto_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = texts.AUTO_RESPONSE_ASK_RESUME

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

    return AUTO_RESPONSE_RESUME


async def ask_auto_response_search_method(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Шаг 2: Выбор способа поиска"""
    query = update.callback_query
    resume_id = query.data.replace("auto_resume_", "")
    context.user_data["auto_response_setup"]["resume_id"] = resume_id
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🔎 Настроить фильтры в боте", callback_data="auto_configure_filters"
            )
        ],
        [InlineKeyboardButton("🌐 Вставить ссылку поиска hh.ru", callback_data="auto_paste_link")],
        [InlineKeyboardButton("🔙 Назад", callback_data="auto_resume_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = texts.AUTO_RESPONSE_ASK_SEARCH_METHOD
    await query.message.edit_text(text, reply_markup=reply_markup)

    return AUTO_RESPONSE_SEARCH_METHOD


async def ask_auto_response_hh_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает ссылку с hh.ru"""
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="auto_search_method_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(texts.AUTO_RESPONSE_ASK_HH_URL, reply_markup=reply_markup)

    return AUTO_RESPONSE_HH_URL


async def handle_auto_response_hh_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ссылку с hh.ru и переходит к выбору сопроводительного письма"""
    url_text = update.message.text

    try:
        parsed_url = urlparse(url_text)
        query_params = parse_qs(parsed_url.query)

        # Сохраняем данные из URL
        setup_data = context.user_data["auto_response_setup"]
        setup_data["search_by_url"] = True
        setup_data["hh_url"] = url_text
        setup_data["keyword"] = query_params.get("text", [""])[0]
        setup_data["area"] = query_params.get("area", [])
        setup_data["schedule"] = query_params.get("schedule", [])
        setup_data["employment"] = query_params.get("employment", [])
        setup_data["profession"] = query_params.get("professional_role", [])
        setup_data["search_fields"] = query_params.get("search_field", [])

        logging.info(f"Parsed auto-response URL. Setup data: {setup_data}")

        # Переходим к выбору сопроводительного письма
        return await ask_auto_response_cover_letter(update, context)

    except Exception as e:
        logging.error(
            f"Failed to parse auto-response HH URL: {url_text}. Error: {e}", exc_info=True
        )
        await update.message.reply_text(
            "Не удалось распознать ссылку. Пожалуйста, убедитесь, что вы скопировали правильную ссылку и попробуйте снова."
        )
        return AUTO_RESPONSE_HH_URL


async def start_auto_response_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает настройку фильтров (переиспользует логику из обычных откликов)"""
    query = update.callback_query
    await query.answer()

    context.user_data["auto_response_setup"]["search_by_url"] = False

    # Используем логику из responses.py для настройки фильтров
    # Переходим к выбору страны
    countries = config.DEMO_COUNTRIES
    context.bot_data["countries"] = countries

    reply_markup = build_paginated_keyboard(countries, page=0, prefix="auto_country")
    await query.message.edit_text("📍 Шаг 3/10:\nВыберите страну поиска", reply_markup=reply_markup)

    return AUTO_RESPONSE_FILTERS


async def ask_auto_response_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 9: Выбор сопроводительного письма"""
    cover_letters = context.user_data.get("cover_letters", [])
    keyboard = []

    # Добавляем существующие сопроводительные письма
    if cover_letters:
        for i, letter in enumerate(cover_letters):
            keyboard.append(
                [InlineKeyboardButton(f"📄 {letter['title']}", callback_data=f"auto_cl_select_{i}")]
            )

    # Добавляем опции
    keyboard.extend(
        [
            [InlineKeyboardButton("✏️ Написать новое письмо", callback_data="auto_cl_write_new")],
            [
                InlineKeyboardButton(
                    "📭 Без сопроводительного письма", callback_data="auto_no_letter"
                )
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="auto_cover_letter_back")],
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "📍 Шаг 9/10:\nВыберите сопроводительное письмо для автооткликов:"

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)

    return AUTO_RESPONSE_COVER_LETTER


async def handle_auto_response_cover_letter_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Обрабатывает выбор сопроводительного письма"""
    query = update.callback_query
    await query.answer()

    if query.data == "auto_no_letter":
        context.user_data["auto_response_setup"]["cover_letter"] = "Без сопроводительного письма"
    elif query.data.startswith("auto_cl_select_"):
        letter_index = int(query.data.split("_")[-1])
        letter = context.user_data["cover_letters"][letter_index]
        context.user_data["auto_response_setup"]["cover_letter"] = letter["body"]
    elif query.data == "auto_cl_write_new":
        await query.message.edit_text("Напишите сопроводительное письмо для автооткликов:")
        context.user_data["waiting_for_auto_cover_letter"] = True
        return AUTO_RESPONSE_COVER_LETTER

    # Переходим к подтверждению
    return await show_auto_response_confirmation(update, context)


async def handle_auto_response_cover_letter_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Обрабатывает текст нового сопроводительного письма"""
    if context.user_data.get("waiting_for_auto_cover_letter", False):
        context.user_data["auto_response_setup"]["cover_letter"] = update.message.text
        context.user_data.pop("waiting_for_auto_cover_letter", None)
        return await show_auto_response_confirmation(update, context, message=update.message)
    else:
        return AUTO_RESPONSE_COVER_LETTER


async def show_auto_response_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, message=None
) -> int:
    """Шаг 10: Подтверждение настроек автооткликов"""
    setup_data = context.user_data["auto_response_setup"]

    # Получаем название резюме
    resume_id = setup_data.get("resume_id")
    resume_title = next(
        (r["title"] for r in config.DEMO_RESUMES if r["id"] == resume_id), "Не указано"
    )

    # Определяем способ поиска
    if setup_data.get("search_by_url"):
        search_method = "По ссылке hh.ru"
        filters_summary = f"Ссылка: {setup_data.get('hh_url', 'Не указано')}"
    else:
        search_method = "Настроенные фильтры"
        filters_summary = "Фильтры настроены в боте"

    # Статус сопроводительного письма
    cover_letter = setup_data.get("cover_letter", "Не указано")
    cover_letter_status = "Да" if cover_letter != "Без сопроводительного письма" else "Нет"

    text = texts.get_auto_response_confirmation(
        resume_title, search_method, filters_summary, cover_letter_status
    )

    keyboard = [
        [InlineKeyboardButton("🚀 Запустить автоотклики", callback_data="auto_start")],
        [InlineKeyboardButton("🔙 Изменить настройки", callback_data="auto_change_settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if message:
        await message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

    return AUTO_RESPONSE_CONFIRMATION


async def start_auto_responses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запускает автоотклики"""
    query = update.callback_query
    await query.answer()

    # Сохраняем настройки автооткликов
    setup_data = context.user_data.pop("auto_response_setup", {})
    context.user_data["auto_response_settings"] = setup_data
    context.user_data["auto_response_active"] = True

    # Добавляем данные о запуске
    now = datetime.now()
    context.user_data["auto_response_settings"]["start_date"] = now.strftime("%d.%m.%Y")
    context.user_data["auto_response_settings"]["start_time"] = now.strftime("%H:%M")
    context.user_data["auto_response_settings"]["today_count"] = 0
    context.user_data["auto_response_settings"]["total_count"] = 0

    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(texts.AUTO_RESPONSE_STARTED, reply_markup=reply_markup)

    return ConversationHandler.END


async def stop_auto_responses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Останавливает автоотклики"""
    query = update.callback_query
    await query.answer()

    context.user_data["auto_response_active"] = False

    keyboard = [
        [InlineKeyboardButton("▶️ Запустить снова", callback_data="auto_restart")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(texts.AUTO_RESPONSE_STOPPED, reply_markup=reply_markup)

    return AUTO_RESPONSE_MAIN


async def restart_auto_responses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Перезапускает автоотклики с сохраненными настройками"""
    query = update.callback_query
    await query.answer()

    context.user_data["auto_response_active"] = True

    # Обновляем время запуска
    now = datetime.now()
    context.user_data["auto_response_settings"]["start_date"] = now.strftime("%d.%m.%Y")
    context.user_data["auto_response_settings"]["start_time"] = now.strftime("%H:%M")

    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(texts.AUTO_RESPONSE_STARTED, reply_markup=reply_markup)

    return ConversationHandler.END


def get_auto_responses_conv_handler():
    """Возвращает conversation handler для автооткликов"""
    from routers import menu, start

    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_auto_responses_main, pattern="^auto_responses$"),
        ],
        states={
            AUTO_RESPONSE_MAIN: [
                CallbackQueryHandler(start_auto_response_setup, pattern="^auto_setup$"),
                CallbackQueryHandler(stop_auto_responses, pattern="^auto_stop$"),
                CallbackQueryHandler(start_auto_response_setup, pattern="^auto_change_settings$"),
                CallbackQueryHandler(restart_auto_responses, pattern="^auto_restart$"),
            ],
            AUTO_RESPONSE_RESUME: [
                CallbackQueryHandler(ask_auto_response_search_method, pattern="^auto_resume_"),
                CallbackQueryHandler(show_auto_responses_main, pattern="^auto_main$"),
            ],
            AUTO_RESPONSE_SEARCH_METHOD: [
                CallbackQueryHandler(
                    start_auto_response_filters, pattern="^auto_configure_filters$"
                ),
                CallbackQueryHandler(ask_auto_response_hh_url, pattern="^auto_paste_link$"),
                CallbackQueryHandler(ask_auto_response_resume, pattern="^auto_resume_back$"),
            ],
            AUTO_RESPONSE_HH_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auto_response_hh_url),
                CallbackQueryHandler(
                    ask_auto_response_search_method, pattern="^auto_search_method_back$"
                ),
            ],
            AUTO_RESPONSE_FILTERS: [
                # Здесь будут обработчики для фильтров (пока заглушка)
                CallbackQueryHandler(ask_auto_response_cover_letter, pattern="^auto_filters_done$"),
            ],
            AUTO_RESPONSE_COVER_LETTER: [
                CallbackQueryHandler(
                    handle_auto_response_cover_letter_selection, pattern="^auto_no_letter$"
                ),
                CallbackQueryHandler(
                    handle_auto_response_cover_letter_selection, pattern=r"^auto_cl_select_\d+$"
                ),
                CallbackQueryHandler(
                    handle_auto_response_cover_letter_selection, pattern="^auto_cl_write_new$"
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_auto_response_cover_letter_text
                ),
            ],
            AUTO_RESPONSE_CONFIRMATION: [
                CallbackQueryHandler(start_auto_responses, pattern="^auto_start$"),
                CallbackQueryHandler(start_auto_response_setup, pattern="^auto_change_settings$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start.start_over),
            CallbackQueryHandler(menu.back_to_main_menu, pattern="^main_menu$"),
        ],
        allow_reentry=True,
    )
