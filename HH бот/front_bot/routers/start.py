# routers/start.py
from __future__ import annotations

import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

log = logging.getLogger(__name__)

# --- callback_data константы
CB_LINK_ACCOUNT = "link_account"
CB_MAIN_MENU = "main_menu"

# --- клавиатуры
MAIN_MENU_KB = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🔗 Привязать аккаунт", callback_data=CB_LINK_ACCOUNT)],
        [InlineKeyboardButton("🏠 В главное меню", callback_data=CB_MAIN_MENU)],
    ]
)

# --- универсальная отправка
async def _send(
    update: Update,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    *,
    prefer_edit: bool = True,
):
    """
    Универсальный ответ:
    - если пришли через callback_query и prefer_edit=True -> edit_text
    - иначе reply_text
    """
    if update.callback_query:
        try:
            await update.callback_query.answer()
        except Exception:
            pass
        if prefer_edit:
            return await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        return await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

    if update.effective_message:
        return await update.effective_message.reply_text(text, reply_markup=reply_markup)

    if update.effective_chat:
        return await update.get_bot().send_message(update.effective_chat.id, text, reply_markup=reply_markup)


# --- общий показ главного меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Это главное меню.\n\n"
        "• Нажми «🔗 Привязать аккаунт», чтобы продолжить.\n"
        "• В любой момент можно вернуться «🏠 В главное меню»."
    )
    await _send(update, text, reply_markup=MAIN_MENU_KB, prefer_edit=True)


# --- публичные хендлеры (ожидаются другими модулями)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start — просто показывает главное меню."""
    await show_main_menu(update, context)


async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Заглушка привязки аккаунта — важна тем, что на неё ссылается main.py.
    Реальную логику можно внедрить позже.
    """
    text = (
        "🔧 Привязка аккаунта пока не реализована.\n"
        "Скоро тут появится форма/ссылка. Используй меню ниже."
    )
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 В главное меню", callback_data=CB_MAIN_MENU)]]
    )
    await _send(update, text, reply_markup=kb, prefer_edit=True)


async def in_development(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для функций в разработке (её импортирует routers.responses)."""
    text = "Эта функция пока в разработке 🛠️"
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 В главное меню", callback_data=CB_MAIN_MENU)]]
    )
    await _send(update, text, reply_markup=kb, prefer_edit=True)


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню из любых состояний."""
    await show_main_menu(update, context)
    return ConversationHandler.END


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Фоллбэк: чистим стейт/джобы и возвращаемся в главное меню."""
    try:
        context.user_data.clear()
        if context.job_queue and update.effective_user:
            for job in context.job_queue.get_jobs_by_name(str(update.effective_user.id)):
                job.schedule_removal()
    except Exception as e:
        log.debug("start_over cleanup issue: %r", e)

    await show_main_menu(update, context)
    return ConversationHandler.END


__all__ = [
    "start",
    "start_over",
    "link_account",
    "in_development",
    "back_to_main_menu",
    "show_main_menu",
]
