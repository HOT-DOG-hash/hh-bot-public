import os
import logging
from pathlib import Path
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

def setup_logging() -> None:
    log_file = os.getenv("BOT_LOG_FILE", "/var/log/app/bot.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
    )

def _get_token():
    return os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

async def post_init(app: Application):
    try:
        await app.bot.set_my_commands(app.bot_data.get("__commands__", []))
    except Exception as e:
        logging.warning("Failed to set bot commands: %s", e)

def build_bot_application(token: str) -> Application:
    application = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Бот запущен (standalone).")

    application.add_handler(CommandHandler("start", start_cmd))
    application.bot_data["__commands__"] = [BotCommand("start", "Начать / Перезапустить")]
    return application

async def main():
    setup_logging()
    token = _get_token()
    if not token:
        raise SystemExit("No TELEGRAM_BOT_TOKEN/BOT_TOKEN provided")
    app = build_bot_application(token)
    # run_polling сам вызовет initialize/start/stop
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
