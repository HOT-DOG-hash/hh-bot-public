from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import texts
from utils.states import COVER_LETTER_MENU, CL_ASK_TITLE, CL_SAVE_BODY, CL_VIEW

async def show_cover_letters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the main menu for cover letters (demo mode)."""
    if 'cover_letters' not in context.user_data:
        context.user_data['cover_letters'] = []

    cover_letters = context.user_data['cover_letters']
    
    text = texts.CL_MENU_HEADER
    
    keyboard = [[InlineKeyboardButton("✏️ Новое сопроводительное письмо", callback_data="cl_new")]]
    for i, letter in enumerate(cover_letters):
        keyboard.append([InlineKeyboardButton(f"📄 {letter['title']}", callback_data=f"cl_view_{i}")])
    
    keyboard.append([InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
        
    return COVER_LETTER_MENU

async def ask_new_cover_letter_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the title of the new cover letter."""
    if len(context.user_data.get('cover_letters', [])) >= 5:
        keyboard = [[InlineKeyboardButton("🔙 Вернуться в список писем", callback_data="cl_back_to_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text(
            texts.CL_LIMIT_REACHED,
            reply_markup=reply_markup
        )
        return COVER_LETTER_MENU

    await update.callback_query.message.edit_text(texts.CL_ASK_TITLE)
    return CL_ASK_TITLE

async def ask_new_cover_letter_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the title and asks for the body."""
    context.user_data['new_cl_title'] = update.message.text[:50]
    await update.message.reply_text(texts.CL_ASK_BODY)
    return CL_SAVE_BODY

async def save_cover_letter_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the new cover letter."""
    title = context.user_data.pop('new_cl_title')
    body = update.message.text
    
    if 'cover_letters' not in context.user_data:
        context.user_data['cover_letters'] = []
        
    context.user_data['cover_letters'].append({'title': title, 'body': body})
    
    keyboard = [[InlineKeyboardButton("🔙 Вернуться в список писем", callback_data="cl_back_to_list")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(texts.CL_SAVED, reply_markup=reply_markup)
    
    return COVER_LETTER_MENU

async def view_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays a specific cover letter and a delete button."""
    query = update.callback_query
    letter_index = int(query.data.split('_')[-1])
    context.user_data['current_cl_index'] = letter_index
    letter = context.user_data['cover_letters'][letter_index]
    
    text = texts.get_cl_view_text(letter['body'])
    
    keyboard = [
        [InlineKeyboardButton("🗑 Удалить сопроводительное письмо", callback_data="cl_delete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="cl_back_to_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup)
    return CL_VIEW

async def delete_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Deletes the selected cover letter."""
    query = update.callback_query
    letter_index = context.user_data.pop('current_cl_index')
    
    del context.user_data['cover_letters'][letter_index]
    
    await query.answer(texts.CL_DELETED)
    
    return await show_cover_letters(update, context)


def get_cover_letter_conv_handler():
    """Returns the cover letter conversation handler."""
    from . import menu, start
    return ConversationHandler(
        entry_points=[
            CommandHandler("response_message", show_cover_letters),
            CallbackQueryHandler(show_cover_letters, pattern="^cover_letters$"),
        ],
        states={
            COVER_LETTER_MENU: [
                CallbackQueryHandler(ask_new_cover_letter_title, pattern="^cl_new$"),
                CallbackQueryHandler(view_cover_letter, pattern=r"^cl_view_\d+$"),
                CallbackQueryHandler(show_cover_letters, pattern="^cl_back_to_list$"),
            ],
            CL_ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_new_cover_letter_body)],
            CL_SAVE_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_cover_letter_body)],
            CL_VIEW: [
                CallbackQueryHandler(delete_cover_letter, pattern="^cl_delete$"),
                CallbackQueryHandler(show_cover_letters, pattern="^cl_back_to_list$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start.start_over),
            CallbackQueryHandler(menu.back_to_main_menu, pattern="^main_menu$"),
        ],
        allow_reentry=True
    )