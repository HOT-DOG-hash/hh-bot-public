from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from sqlalchemy import text
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from backend.app.core.db import get_engine

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass


def setup_logging() -> None:
    log_file = os.getenv("BOT_LOG_FILE", "/var/log/app/app.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)


def _get_token() -> Optional[str]:
    return os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")


def build_bot_application(token: str) -> Application:
    application = Application.builder().token(token).build()

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text("Бот запущен. Команды временно упрощены.")

    application.add_handler(CommandHandler("start", start_cmd))
    application.bot_data["__commands__"] = [BotCommand("start", "Начать / Перезапустить")]
    return application


async def start_bot(app_: FastAPI) -> None:
    token = _get_token()
    if not token:
        logging.info("Telegram token is missing - bot disabled.")
        app_.state.bot_state = {"running": False, "reason": "no-token"}
        return

    application = build_bot_application(token)
    await application.initialize()
    try:
        await application.bot.set_my_commands(application.bot_data.get("__commands__", []))
    except Exception as exc:  # pragma: no cover - defensive
        logging.warning("Failed to set bot commands: %s", exc)

    await application.start()
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
        except Exception:  # pragma: no cover - depends on PTB internals
            pass
        await application.stop()
        await application.shutdown()
        logging.info("Telegram bot stopped.")
    finally:
        app_.state.bot_state = {"running": False}
        app_.state.ptb_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    if os.getenv("ENABLE_TELEGRAM_BOT", "0") == "1":
        await start_bot(app)
    else:
        logging.info("Telegram bot disabled (ENABLE_TELEGRAM_BOT!=1).")
    try:
        yield
    finally:
        await stop_bot(app)


app = FastAPI(title="HH Bot API", lifespan=lifespan)


@app.on_event("startup")
async def startup_ping() -> None:
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logging.info("Database connectivity check passed.")
    except Exception as exc:  # pragma: no cover - fail fast in prod
        logging.exception("Database connectivity check failed: %s", exc)
        raise


from .routers import admin as admin_router  # noqa: E402
from .routers import health as health_router  # noqa: E402

app.include_router(admin_router.router, prefix="")
app.include_router(health_router.router, prefix="")

try:
    from .routers.health import health as health_ep, healthz as healthz_ep  # type: ignore # noqa: E402

    app.add_api_route("/health", endpoint=health_ep, methods=["GET"], name="health_root_alias")
    app.add_api_route("/healthz", endpoint=healthz_ep, methods=["GET"], name="healthz_root_alias")
    app.add_api_route("/api/health", endpoint=health_ep, methods=["GET"], name="health_api_alias")
    app.add_api_route("/api/healthz", endpoint=healthz_ep, methods=["GET"], name="healthz_api_alias")
except Exception as exc:  # pragma: no cover - keeps API up even if optional router fails
    logging.warning("Health aliases not set: %s", exc)


@app.get("/", tags=["meta"])
def root():
    return {"app": "hh-bot", "status": "ok", "version": os.getenv("APP_VERSION", "dev")}


@app.get("/version", tags=["meta"])
def version():
    return {"version": os.getenv("APP_VERSION", "dev")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("WEB_PORT", "8000")),
        reload=False,
    )
