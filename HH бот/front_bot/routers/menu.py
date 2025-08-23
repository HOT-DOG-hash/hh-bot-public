from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import texts

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates and returns the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🚀 Запустить отклики", callback_data="start_responses")],
        [InlineKeyboardButton("📎 Автоотклики по параметрам", callback_data="auto_responses")],
        [InlineKeyboardButton("📄 Сопроводительные письма", callback_data="cover_letters")],
        [InlineKeyboardButton("💳 Подписка", callback_data="subscription")],
        [InlineKeyboardButton("📊 Статистика откликов", callback_data="stats")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support")],
        [InlineKeyboardButton("👥 Реферальная программа", callback_data="referral")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int = None) -> None:
    """Displays the main menu."""
    reply_markup = get_main_menu_keyboard()
    text = texts.MAIN_MENU_TITLE
    
    if update and update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    elif update:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif chat_id:
        # This case is for calling from external sources
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await main_menu(update, context)
    return ConversationHandler.END

async def show_referral_program(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the referral program information."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    # Demo data
    level1_referrals = 5
    level2_referrals = 12
    level3_referrals = 3
    total_income = 2500
    balance = 1200
    min_withdrawal = 500

    text = texts.get_referral_text(
        referral_link,
        level1_referrals,
        level2_referrals,
        level3_referrals,
        total_income,
        balance,
        min_withdrawal
    )

    keyboard = [[InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.answer()
        await query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows subscription status and options (demo mode)."""
    subscription_status = context.user_data.get("subscription_status", "active")  # По умолчанию активна в демо
    
    text = texts.SUBSCRIPTION_INFO

    if subscription_status == "active":
        text += f"**Ваш статус:**\n{texts.SUBSCRIPTION_ACTIVE}"
    else:
        text += f"**Ваш статус:**\n{texts.SUBSCRIPTION_INACTIVE}"

    keyboard = [
        [InlineKeyboardButton("Неделя — 690₽", callback_data="pay_week")],
        [InlineKeyboardButton("Месяц — 1900₽", callback_data="pay_month")],
        [InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_payment_stub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the stub for payment processing (demo mode)."""
    query = update.callback_query
    await query.answer()
    
    context.user_data["subscription_status"] = "active"
    
    text = texts.SUBSCRIPTION_SUCCESS
    keyboard = [[InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup)

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays support information (demo mode)."""
    support_text = texts.SUPPORT_INFO
    
    keyboard = [[InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(support_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(support_text, reply_markup=reply_markup)