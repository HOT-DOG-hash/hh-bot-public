# HH бот/backend/app/main.py
import os
import secrets
import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# python-telegram-bot 20.x
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# подхват .env (не обязателен, но удобно)
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
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


# ------------------------------
# FASTAPI
# ------------------------------
app = FastAPI(title="HH Bot API (hybrid)")

security = HTTPBasic()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    ok_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    ok_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/health")
def health():
    info = {"status": "ok"}
    bot_state = getattr(app.state, "bot_state", None)
    info["bot"] = "running" if bot_state and bot_state.get("running") else "stopped"
    return info


@app.get("/admin/ping")
def admin_ping(_: str = Depends(require_admin)):
    return {"ok": True}


# Попробуем (необязательно) подключить дополнительные роутеры, если они есть
try:
    from .routers import bot_api, admin_api  # type: ignore

    app.include_router(bot_api.router, prefix="/api/bot")
    app.include_router(admin_api.router, prefix="/api/admin")
except Exception as e:
    logging.warning("Optional routers weren't loaded: %s", e)


# ------------------------------
# TELEGRAM BOT (минимальная рабочая версия)
# ------------------------------
def _get_token() -> Optional[str]:
    # приоритет: окружение / .env
    return os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")


def build_bot_application(token: str) -> Application:
    """Минимальная версия PTB Application без внешних зависимостей."""
    application = Application.builder().token(token).build()

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Бот запущен. Команды временно упрощены.")

    application.add_handler(CommandHandler("start", start_cmd))

    commands = [BotCommand("start", "Начать / Перезапустить")]
    application.bot_data["__commands__"] = commands
    return application


async def start_bot(app_: FastAPI) -> None:
    """Инициализирует и запускает polling внутри процесса FastAPI."""
    setup_logging()

    token = _get_token()
    if not token:
        logging.warning(
            "Telegram token is missing. Bot will NOT start. "
            "Set TELEGRAM_BOT_TOKEN or BOT_TOKEN env (can be in .env)."
        )
        app_.state.bot_state = {"running": False, "reason": "no-token"}
        return

    application = build_bot_application(token)

    # Запуск PTB 20.x без блокировки FastAPI
    await application.initialize()
    try:
        await application.bot.set_my_commands(application.bot_data.get("__commands__", []))
    except Exception as e:
        logging.warning("Failed to set bot commands: %s", e)

    await application.start()

    # В PTB 20.x polling может жить внутри Application.
    # В обычном случае доступен application.updater.start_polling(...)
    try:
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)  # type: ignore[attr-defined]
    except Exception:
        # Если атрибут updater недоступен в сборке, сделаем безопасный fallback
        asyncio.create_task(application.run_polling(allowed_updates=Update.ALL_TYPES))

    # Сохраняем в state, чтобы корректно останавливать
    app_.state.ptb_app = application
    app_.state.bot_state = {"running": True}
    logging.info("Telegram bot started (polling).")


async def stop_bot(app_: FastAPI) -> None:
    """Останавливает polling и корректно завершает PTB."""
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
# ХУКИ ЖИЗНЕННОГО ЦИКЛА FASTAPI
# ------------------------------
@app.on_event("startup")
async def _on_startup():
    if os.getenv("ENABLE_TELEGRAM_BOT", "0") == "1":
        await start_bot(app)
    else:
        logging.info("Telegram bot disabled (ENABLE_TELEGRAM_BOT!=1).")


@app.on_event("shutdown")
async def _on_shutdown():
    await stop_bot(app)


# Локальный запуск (обычно используешь uvicorn внешне)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("WEB_PORT", "8000")),
        reload=False,
    )
