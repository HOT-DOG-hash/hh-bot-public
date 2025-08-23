from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import texts, states
import random
from datetime import datetime

def get_demo_resumes():
    """Возвращает демо-данные резюме пользователя."""
    return [
        {"id": 1, "name": "Python разработчик"},
        {"id": 2, "name": "Frontend разработчик"},
        {"id": 3, "name": "Data Analyst"},
    ]

def get_demo_stats(resume_id):
    """Возвращает демо-статистику для резюме."""
    # Генерируем случайные, но реалистичные данные
    total_responses = random.randint(50, 200)
    responses_today = random.randint(0, 15)
    invites = random.randint(5, total_responses // 4)
    declines = random.randint(invites, total_responses - invites)
    
    return {
        "total_responses": total_responses,
        "responses_today": responses_today,
        "invites": invites,
        "declines": declines
    }

async def show_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает меню выбора резюме для статистики."""
    resumes = get_demo_resumes()
    
    if not resumes:
        # Если нет резюме
        keyboard = [[InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(
                texts.STATS_NO_RESUMES,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                texts.STATS_NO_RESUMES,
                reply_markup=reply_markup
            )
        return ConversationHandler.END
    
    # Создаем кнопки для каждого резюме
    keyboard = []
    for resume in resumes:
        keyboard.append([InlineKeyboardButton(
            resume["name"], 
            callback_data=f"stats_resume_{resume['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            texts.STATS_SELECT_RESUME,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            texts.STATS_SELECT_RESUME,
            reply_markup=reply_markup
        )
    
    return states.STATS_SELECT_RESUME

async def show_resume_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает статистику для выбранного резюме."""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем ID резюме из callback_data
    resume_id = int(query.data.split("_")[-1])
    
    # Получаем данные резюме и статистику
    resumes = get_demo_resumes()
    resume = next((r for r in resumes if r["id"] == resume_id), None)
    
    if not resume:
        await query.message.reply_text("Резюме не найдено.")
        return ConversationHandler.END
    
    stats = get_demo_stats(resume_id)
    
    # Формируем текст статистики
    stats_text = texts.get_stats_text(
        resume["name"],
        stats["total_responses"],
        stats["responses_today"],
        stats["invites"],
        stats["declines"]
    )
    
    keyboard = [[InlineKeyboardButton(texts.BACK_TO_MAIN_MENU, callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        stats_text,
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возвращает в главное меню."""
    from routers import menu
    await menu.main_menu(update, context)
    return ConversationHandler.END

def get_stats_conv_handler():
    """Создает и возвращает ConversationHandler для статистики."""
    from telegram.ext import CallbackQueryHandler
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_stats_menu, pattern="^stats$")
        ],
        states={
            states.STATS_SELECT_RESUME: [
                CallbackQueryHandler(show_resume_stats, pattern="^stats_resume_"),
                CallbackQueryHandler(back_to_main_menu, pattern="^main_menu$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main_menu, pattern="^main_menu$"),
        ],
    )