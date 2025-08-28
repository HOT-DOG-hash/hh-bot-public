import os
import asyncio
import logging
from pathlib import Path
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

import config
from routers import menu, start, letters, responses, auto_responses, stats

def setup_logging():
    log_file = os.getenv("BOT_LOG_FILE", "/var/log/app/bot.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

async def main() -> None:
    """Run the bot."""
    setup_logging()

    # --- Token with fallback ---
    token = getattr(config, "TELEGRAM_BOT_TOKEN", None) or os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Telegram token is missing. Set config.TELEGRAM_BOT_TOKEN or BOT_TOKEN env."
        )

    # --- Persistence ---
    persistence = PicklePersistence(filepath="demo_bot_persistence")

    # --- Application Setup ---
    application = (
        Application.builder()
        .token(token)
        .persistence(persistence)
        .build()
    )

    # --- Command setup ---
    commands = [
        BotCommand("start", "Начать / Перезапустить"),
        BotCommand("menu", "Главное меню 🧭"),
        BotCommand("responses", "Запустить отклики 🚀"),
        BotCommand("response_message", "Сопроводительные письма ✉️"),
    ]
    await application.bot.set_my_commands(commands)

    # --- Conversation Handlers ---
    responses_conv = responses.get_responses_conv_handler()
    cover_letter_conv = letters.get_cover_letter_conv_handler()
    auto_responses_conv = auto_responses.get_auto_responses_conv_handler()
    stats_conv = stats.get_stats_conv_handler()

    # --- Register handlers ---
    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("menu", menu.main_menu))
    application.add_handler(responses_conv)
    application.add_handler(cover_letter_conv)
    application.add_handler(auto_responses_conv)
    application.add_handler(stats_conv)
    application.add_handler(CallbackQueryHandler(start.link_account, pattern="^link_account$"))
    application.add_handler(CallbackQueryHandler(menu.show_subscription, pattern="^subscription$"))
    application.add_handler(CallbackQueryHandler(menu.handle_payment_stub, pattern=r"^pay_(week|month)$"))
    application.add_handler(CallbackQueryHandler(menu.show_support, pattern="^support$"))
    application.add_handler(CallbackQueryHandler(menu.show_referral_program, pattern="^referral$"))
    application.add_handler(CallbackQueryHandler(menu.main_menu, pattern="^main_menu$"))

    # --- Start polling ---
    async with application:
        await application.initialize()
        logging.info("Demo bot started successfully!")
        await application.start()
        await application.updater.start_polling()

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logging.info("Received stop signal")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Demo bot stopped.")
