from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy import text
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from backend.app.core.db import get_engine

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

BACKEND_URL = (os.getenv("BACKEND_URL") or "http://web:8000").rstrip("/")
HTTP_TIMEOUT = float(os.getenv("BOT_HTTP_TIMEOUT", "10"))
PLANS: dict[str, dict[str, Any]] = {
    "premium-week": {
        "title": "Неделя — 690 ₽ / 7 дней",
        "plan": "premium-week",
        "price": "690 ₽",
        "duration_days": 7,
    },
    "premium-month": {
        "title": "Месяц — 1900 ₽ / 30 дней",
        "plan": "premium-month",
        "price": "1900 ₽",
        "duration_days": 30,
    },
}
PLAN_ORDER: list[str] = ["premium-week", "premium-month"]

logger = logging.getLogger("bot.commands")


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


def _get_token() -> str | None:
    return os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")


def build_bot_application(token: str) -> Application:
    application = Application.builder().token(token).build()

    class BackendError(RuntimeError):
        def __init__(self, status: int, message: str | None = None) -> None:
            super().__init__(message or "")
            self.status = status
            self.detail = message or ""

    def describe_error(error: BackendError) -> str:
        if error.status == 402:
            return "Подписка не активна. Оформите премиум, чтобы продолжить."
        if error.status == 404:
            return "Данные не найдены. Наберите /premium, чтобы начать заново."
        if error.status == 400:
            return "Запрос отклонён. Проверьте параметры и попробуйте ещё раз."
        if error.status >= 500:
            return "Сервис занят, попробуйте позже."
        return "Сервис недоступен, попробуйте позже."

    async def request_backend(
        method: str,
        path: str,
        chat_id: int,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{BACKEND_URL}{path}"
        headers = {"X-User-Id": str(chat_id)}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                response = await client.request(method, url, params=params, headers=headers)
            except httpx.RequestError as exc:
                logger.warning("bot_backend_unavailable", error=str(exc))
                raise RuntimeError("Сервис занят, попробуйте позже.") from exc

        if response.status_code >= 500:
            logger.warning("bot_backend_http_error", status=response.status_code, path=path)
            raise RuntimeError("Сервис занят, попробуйте позже.")
        if response.status_code >= 400:
            detail = None
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = payload.get("detail") or payload.get("message")
            except ValueError:
                detail = None
            raise BackendError(response.status_code, detail or "")

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def normalize_plan(value: str | None) -> str | None:
        if not value:
            return None
        key = value.strip().lower()
        return key if key in PLANS else None

    def plan_title(plan_code: str | None) -> str:
        if not plan_code:
            return "премиум"
        info = PLANS.get(plan_code)
        return info.get("title", plan_code) if info else plan_code

    def build_plans_text() -> str:
        lines = [f"• {PLANS[code]['title']}" for code in PLAN_ORDER]
        return "Доступные тарифы:\n" + "\n".join(lines)

    def build_benefits_text() -> str:
        return (
            "Что даёт премиум:\n"
            "• свежие вакансии и фильтры по важным критериям;\n"
            "• автоматические отклики и шаблоны писем;\n"
            "• помощь с обновлением резюме и приоритетную поддержку."
        )

    def build_buy_keyboard(include_status: bool = True) -> InlineKeyboardMarkup:
        rows = [
            [InlineKeyboardButton("Купить неделю", callback_data="buy:premium-week")],
            [InlineKeyboardButton("Купить месяц", callback_data="buy:premium-month")],
        ]
        if include_status:
            rows.append([InlineKeyboardButton("Статус подписки", callback_data="status")])
        return InlineKeyboardMarkup(rows)

    def format_until(raw: Any) -> str:
        if not raw:
            return "без даты окончания"
        if isinstance(raw, str):
            value = raw
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
            except ValueError:
                return raw
        return str(raw)

    async def fetch_subscription(chat_id: int) -> dict[str, Any]:
        return await request_backend("GET", "/billing/subscription", chat_id)

    async def send_status(chat_id: int, send: Callable[..., Awaitable[Any]]) -> None:
        try:
            data = await fetch_subscription(chat_id)
        except BackendError as exc:
            await send(describe_error(exc), reply_markup=build_buy_keyboard())
            return
        except RuntimeError as exc:
            await send(str(exc))
            return

        if data.get("active"):
            plan_label = plan_title(data.get("plan"))
            until = format_until(data.get("until"))
            await send(f"Подписка активна: {plan_label}.\nДействует до {until}.")
        else:
            await send(
                "Подписка не активна. Выберите тариф и оформите премиум.",
                reply_markup=build_buy_keyboard(),
            )

    async def send_buy_link(
        chat_id: int, plan_code: str, send: Callable[..., Awaitable[Any]]
    ) -> None:
        if plan_code not in PLANS:
            await send(
                "Неизвестный тариф. Доступны: premium-week или premium-month.",
                reply_markup=build_buy_keyboard(include_status=False),
            )
            return
        try:
            data = await request_backend(
                "POST", "/billing/create", chat_id, params={"plan": plan_code}
            )
        except BackendError as exc:
            await send(describe_error(exc))
            return
        except RuntimeError as exc:
            await send(str(exc))
            return

        pay_url = data.get("pay_url")
        if not pay_url:
            await send("Не удалось получить ссылку на оплату. Попробуйте позже.")
            return
        await send(
            f"Ссылка на оплату ({plan_title(plan_code)}):\n{pay_url}\n"
            "После оплаты наберите /status, чтобы проверить подписку."
        )

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(
                "Привет! Загляни в /premium, чтобы выбрать тариф и узнать преимущества."
            )

    async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        chat_id = update.effective_chat.id
        try:
            data = await fetch_subscription(chat_id)
        except BackendError as exc:
            status_text = describe_error(exc)
        except RuntimeError as exc:
            status_text = str(exc)
        else:
            if data.get("active"):
                status_text = (
                    f"Подписка активна: {plan_title(data.get('plan'))}.\n"
                    f"Действует до {format_until(data.get('until'))}."
                )
            else:
                status_text = "Подписка пока не активна."

        message = f"{build_plans_text()}\n\n" f"{build_benefits_text()}\n\n" f"{status_text}"
        await update.message.reply_text(message, reply_markup=build_buy_keyboard())

    async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        chat_id = update.effective_chat.id
        args = context.args or []
        plan_code = normalize_plan(args[0] if args else None)
        if not plan_code:
            await update.message.reply_text(
                "Укажите тариф: /buy premium-week или /buy premium-month.",
                reply_markup=build_buy_keyboard(include_status=False),
            )
            return
        await send_buy_link(chat_id, plan_code, update.message.reply_text)

    async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        chat_id = update.effective_chat.id
        await send_status(chat_id, update.message.reply_text)

    async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        chat_id = update.effective_chat.id
        query_text = " ".join(context.args or []).strip()
        if not query_text:
            await update.message.reply_text(
                "Укажите текст запроса, например /jobs python разработчик."
            )
            return
        try:
            data = await request_backend(
                "GET",
                "/jobs/search",
                chat_id,
                params={"q": query_text, "per_page": 5},
            )
        except BackendError as exc:
            if exc.status == 402:
                await update.message.reply_text(
                    "Поиск доступен только с активной подпиской.",
                    reply_markup=build_buy_keyboard(),
                )
                return
            await update.message.reply_text(describe_error(exc))
            return
        except RuntimeError as exc:
            await update.message.reply_text(str(exc))
            return

        items = data.get("items") or []
        if not items:
            await update.message.reply_text(
                "Пока нет подходящих вакансий. Попробуйте изменить запрос."
            )
            return

        snippets: list[str] = []
        for item in items[:5]:
            title = item.get("name") or "Вакансия"
            employer = item.get("employer") if isinstance(item, dict) else None
            company = employer.get("name") if isinstance(employer, dict) else None
            url = item.get("alternate_url") or item.get("url")
            snippet = f"• {title}"
            if company:
                snippet += f" — {company}"
            if url:
                snippet += f"\n  {url}"
            snippets.append(snippet)

        found = data.get("found")
        header = f"Нашлось {found} вакансий." if isinstance(found, int) else "Свежие вакансии:"
        await update.message.reply_text(f"{header}\n\n" + "\n\n".join(snippets))

    async def buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        await query.answer()
        data = (query.data or "").strip()
        chat = update.effective_chat
        if not chat:
            return
        chat_id = chat.id

        async def send(text: str, reply_markup: InlineKeyboardMarkup | None = None):
            if query.message:
                return await query.message.reply_text(text, reply_markup=reply_markup)
            return await context.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup
            )

        if data.startswith("buy:"):
            plan_code = normalize_plan(data.split(":", 1)[1])
            if not plan_code:
                await send(
                    "Неизвестный тариф. Попробуйте ещё раз.",
                    reply_markup=build_buy_keyboard(),
                )
                return
            await send_buy_link(chat_id, plan_code, send)
        elif data == "status":
            await send_status(chat_id, send)

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("premium", premium_cmd))
    application.add_handler(CommandHandler("buy", buy_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("jobs", jobs_cmd))
    application.add_handler(CallbackQueryHandler(buttons_handler, pattern="^(buy:|status$)"))
    application.bot_data["__commands__"] = [
        BotCommand("start", "Приветствие"),
        BotCommand("premium", "Тарифы и преимущества"),
        BotCommand("buy", "Оплата премиума"),
        BotCommand("status", "Статус подписки"),
        BotCommand("jobs", "Поиск вакансий (нужна подписка)"),
    ]
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
    application: Application | None = getattr(app_.state, "ptb_app", None)
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
from .routers import apply as apply_router  # noqa: E402
from .routers import billing as billing_router  # noqa: E402
from .routers import bot_api as bot_router  # noqa: E402
from .routers import health as health_router  # noqa: E402
from .routers import jobs as jobs_router  # noqa: E402
from .routers import oauth_hh as oauth_hh_router  # noqa: E402
from .routers import payments as payments_router  # noqa: E402

app.include_router(admin_router.router, prefix="")
app.include_router(health_router.router, prefix="")
app.include_router(oauth_hh_router.router, prefix="")
app.include_router(bot_router.router, prefix="/api/bot")
app.include_router(jobs_router.router, prefix="")
app.include_router(billing_router.router, prefix="")
app.include_router(apply_router.router, prefix="")
app.include_router(payments_router.router, prefix="")

try:
    from .routers.health import health as health_ep  # type: ignore # noqa: E402
    from .routers.health import healthz as healthz_ep

    app.add_api_route("/health", endpoint=health_ep, methods=["GET"], name="health_root_alias")
    app.add_api_route("/healthz", endpoint=healthz_ep, methods=["GET"], name="healthz_root_alias")
    app.add_api_route("/api/health", endpoint=health_ep, methods=["GET"], name="health_api_alias")
    app.add_api_route(
        "/api/healthz", endpoint=healthz_ep, methods=["GET"], name="healthz_api_alias"
    )
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
