import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import texts
from routers import menu

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    context.user_data.clear()
    chat_id = update.effective_chat.id

    if context.args:
        try:
            referrer_id = int(context.args[0])
            logger.info(f"User {chat_id} was referred by {referrer_id}")
            context.user_data['referrer_id'] = referrer_id
        except (ValueError, IndexError):
            logger.warning(f"Invalid referral code received: {context.args}")

    # Проверяем, привязан ли аккаунт
    if context.user_data.get('account_linked'):
        # Если аккаунт уже привязан, показываем главное меню
        await menu.main_menu(update, context)
    else:
        # Показываем приветствие с кнопкой привязки аккаунта
        keyboard = [[InlineKeyboardButton("🔗 Привязать аккаунт на HH", callback_data="link_account")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            texts.WELCOME,
            reply_markup=reply_markup,
        )

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulates account linking."""
    query = update.callback_query
    await query.answer()
    
    # Имитируем успешную привязку аккаунта
    context.user_data['account_linked'] = True
    
    await query.message.edit_text(texts.ACCOUNT_LINKED)
    
    # Показываем главное меню через 1 секунду
    import asyncio
    await asyncio.sleep(1)
    await menu.main_menu(update, context)

async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current action and returns to the start menu."""
    await update.message.reply_text(texts.CANCEL_ACTION)
    await start(update, context)
    return ConversationHandler.END

async def in_development(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = texts.IN_DEVELOPMENT
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(message)
    await menu.main_menu(update, context)
    if update.callback_query:
         await query.message.delete()
