from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from backend.app.core.db import get_session_factory
from backend.app.core.startup_checks import check_db, check_redis, ensure_no_placeholders
from backend.app.telemetry.metrics import hydrate_active_campaigns

try:
    from dotenv import load_dotenv

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
    updater = application.updater
    if updater is not None:
        await updater.start_polling(allowed_updates=Update.ALL_TYPES)
    else:
        logging.error("Application updater is unavailable; Telegram bot polling skipped.")

    app_.state.ptb_app = application
    app_.state.bot_state = {"running": True}
    logging.info("Telegram bot started (polling).")


async def stop_bot(app_: FastAPI) -> None:
    application: Optional[Application] = getattr(app_.state, "ptb_app", None)
    if not application:
        app_.state.bot_state = {"running": False}
        return
    try:
        updater = application.updater
        if updater is not None:
            try:
                await updater.stop()
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
    try:
        ensure_no_placeholders()
    except Exception as exc:
        logging.exception("Startup ENV checks failed: %s", exc)
        raise
    if os.getenv("ENABLE_TELEGRAM_BOT", "0") == "1":
        await start_bot(app)
    else:
        logging.info("Telegram bot disabled (ENABLE_TELEGRAM_BOT!=1).")
    try:
        yield
    finally:
        await stop_bot(app)


app = FastAPI(title="HH Bot API", lifespan=lifespan)
app.state.campaigns_enabled = os.getenv("CAMPAIGNS_ENABLED", "0") == "1"


@app.on_event("startup")
async def startup_ping() -> None:
    try:
        await check_db()
        logging.info("Database connectivity check passed.")
        redis_state = await check_redis()
        if redis_state == "ready":
            logging.info("Redis connectivity check passed.")
        else:
            logging.info("Redis check skipped (REDIS_URL not configured).")
        session_factory = get_session_factory()
        async with session_factory() as session:
            await hydrate_active_campaigns(session)
            logging.info("Hydrated campaign metrics gauge from database state.")
    except Exception as exc:  # pragma: no cover - fail fast in prod
        logging.exception("Database connectivity check failed: %s", exc)
        raise


from .routers import admin as admin_router  # noqa: E402
from .routers import admin_api as admin_api_router  # noqa: E402
from .routers import auto_campaigns as auto_campaigns_router  # noqa: E402
from .routers import billing as billing_router  # noqa: E402
from .routers import health as health_router  # noqa: E402
from .routers import metrics as metrics_router  # noqa: E402
from .routers import payments as payments_router  # noqa: E402
from .routers import quota as quota_router  # noqa: E402
from .routers import readyz as readyz_router  # noqa: E402
from .routers import resumes as resumes_router  # noqa: E402
from .routers import bot_api as bot_api_router  # noqa: E402

app.include_router(admin_router.router, prefix="")
app.include_router(admin_api_router.router, prefix="")
app.include_router(auto_campaigns_router.router, prefix="")
app.include_router(billing_router.router, prefix="")
app.include_router(health_router.router, prefix="")
app.include_router(metrics_router.router, prefix="")
app.include_router(payments_router.router, prefix="")
app.include_router(quota_router.router, prefix="")
app.include_router(readyz_router.router, prefix="")
app.include_router(resumes_router.router, prefix="")
app.include_router(bot_api_router.router, prefix="/api/bot")

try:
    from .routers.health import health as health_ep, healthz as healthz_ep   # noqa: E402

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










