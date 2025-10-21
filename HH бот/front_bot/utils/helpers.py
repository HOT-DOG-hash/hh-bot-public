from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


def build_multi_choice_keyboard(
    options: dict, selection_key: str, prefix: str, context: ContextTypes.DEFAULT_TYPE
):
    selected = context.user_data.get(selection_key, set())
    all_selected = selected == set(options.keys())

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'🟢' if all_selected else '🔴'} Выбрать все", callback_data=f"{prefix}_all"
            )
        ]
    ]
    for key, text in options.items():
        status = "🟢" if key in selected else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status} {text}", callback_data=f"{prefix}_{key}")])
    keyboard.append([InlineKeyboardButton("Далее", callback_data=f"{prefix}_next")])
    return InlineKeyboardMarkup(keyboard)


async def handle_multi_choice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    options: dict,
    selection_key: str,
    prefix: str,
):
    query = update.callback_query
    choice = query.data.replace(f"{prefix}_", "")
    await query.answer()

    selected = context.user_data.get(selection_key, set())
    all_options = set(options.keys())

    if choice == "all":
        if selected == all_options:
            selected.clear()
        else:
            selected.update(all_options)
    elif choice in selected:
        selected.remove(choice)
    else:
        selected.add(choice)

    context.user_data[selection_key] = selected
    reply_markup = build_multi_choice_keyboard(options, selection_key, prefix, context)
    await query.edit_message_reply_markup(reply_markup=reply_markup)


def build_paginated_keyboard(
    items: list,
    page: int,
    prefix: str,
    selection_key: str = None,
    context: ContextTypes.DEFAULT_TYPE = None,
    page_size: int = 9,
    add_select_all: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с пагинацией для списка элементов, опционально с множественным выбором.
    """
    keyboard = []

    # Кнопка "Выбрать все"
    if add_select_all and context:
        selected = context.user_data.get(selection_key, set())
        all_ids = {str(item["id"]) for item in items}
        all_selected = selected.issuperset(all_ids)
        status = "🟢" if all_selected else "🔴"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{status} Выбрать все", callback_data=f"page_{prefix}_select_all"
                )
            ]
        )

    total_pages = (len(items) + page_size - 1) // page_size
    start_offset = page * page_size
    end_offset = start_offset + page_size

    # Кнопки элементов
    selected_on_page = context.user_data.get(selection_key, set()) if context else set()
    for item in items[start_offset:end_offset]:
        item_id = str(item["id"])
        status = "🟢" if item_id in selected_on_page else "🔴"
        text = f"{status} {item['name']}" if add_select_all else item["name"]
        keyboard.append([InlineKeyboardButton(text, callback_data=f"{prefix}_{item_id}")])

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{prefix}_nav_{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{prefix}_nav_{page + 1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка "Далее" для режимов с выбором
    if add_select_all:
        keyboard.append([InlineKeyboardButton("Далее", callback_data=f"{prefix}_next")])

    return InlineKeyboardMarkup(keyboard)
