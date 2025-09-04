# backend/app/main.py
from __future__ import annotations

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

# python-telegram-bot 20.x
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# .env подхват (опционально)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# ------------------------------
# ЛОГИ
# ------------------------------
def setup_logging() -> None:
    log_file = os.getenv("BOT_LOG_FILE", "/var/log/app/bot.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
    )

# ------------------------------
# TELEGRAM BOT helpers
# ------------------------------
def _get_token() -> Optional[str]:
    return os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

def build_bot_application(token: str) -> Application:
    application = Application.builder().token(token).build()

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Бот запущен. Команды временно упрощены.")

    application.add_handler(CommandHandler("start", start_cmd))
    commands = [BotCommand("start", "Начать / Перезапустить")]
    application.bot_data["__commands__"] = commands
    return application

async def start_bot(app_: FastAPI) -> None:
    setup_logging()

    token = _get_token()
    if not token:
        logging.info("Telegram token is missing — bot disabled.")
        app_.state.bot_state = {"running": False, "reason": "no-token"}
        return

    application = build_bot_application(token)

    await application.initialize()
    try:
        await application.bot.set_my_commands(application.bot_data.get("__commands__", []))
    except Exception as e:
        logging.warning("Failed to set bot commands: %s", e)

    await application.start()

    # попытка использовать updater (если доступен в твоей сборке)
    try:
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)  # type: ignore[attr-defined]
    except Exception:
        asyncio.create_task(application.run_polling(allowed_updates=Update.ALL_TYPES))

    app_.state.ptb_app = application
    app_.state.bot_state = {"running": True}
    logging.info("Telegram bot started (polling).")

async def stop_bot(app_: FastAPI) -> None:
    application: Optional[Application] = getattr(app_.state, "ptb_app", None)
    if not application:
        app_.state.bot_state = {"running": False}
        return
    try:
        try:
            await application.updater.stop()  # type: ignore[attr-defined]
        except Exception:
            pass
        await application.stop()
        await application.shutdown()
        logging.info("Telegram bot stopped.")
    finally:
        app_.state.bot_state = {"running": False}
        app_.state.ptb_app = None

# ------------------------------
# LIFESPAN (вместо on_event)
# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    if os.getenv("ENABLE_TELEGRAM_BOT", "0") == "1":
        await start_bot(app)
    else:
        logging.info("Telegram bot disabled (ENABLE_TELEGRAM_BOT!=1).")
    try:
        yield
    finally:
        # shutdown
        await stop_bot(app)

# ------------------------------
# APP и роутеры
# ------------------------------
app = FastAPI(title="HH Bot API", lifespan=lifespan)

# Основные роутеры
from .routers import admin as admin_router
from .routers import health as health_router

app.include_router(admin_router.router, prefix="")   # /admin/...
app.include_router(health_router.router, prefix="")  # /health, /healthz

# Дополнительные роутеры (не критично, если их нет)
try:
    from .routers import bot_api, admin_api  # type: ignore
    app.include_router(bot_api.router, prefix="/api/bot")
    app.include_router(admin_api.router, prefix="/api/admin")
except Exception as e:
    logging.warning("Optional routers weren't loaded: %s", e)

# Локальный запуск (обычно используешь uvicorn извне)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("WEB_PORT", "8000")),
        reload=False,
    )
