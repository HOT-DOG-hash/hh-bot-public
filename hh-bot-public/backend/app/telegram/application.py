from __future__ import annotations

import httpx
from typing import Any, Awaitable, Callable, Coroutine, Dict, cast

from fastapi import FastAPI
from httpx import ASGITransport
from telegram import BotCommand
from telegram.ext import Application

from front_bot import register_handlers
from front_bot.api import BackendApi


async def _close_api_client(application: Application) -> None:
    client: httpx.AsyncClient | None = application.bot_data.pop("_api_httpx_client", None)
    if client is not None:
        await client.aclose()


ASGIScope = Dict[str, Any]
ASGIReceive = Callable[[], Awaitable[Dict[str, Any]]]
ASGISend = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
ASGIApp = Callable[[ASGIScope, ASGIReceive, ASGISend], Coroutine[Any, Any, None]]


def build_application(token: str, fastapi_app: FastAPI) -> Application:
    application = Application.builder().token(token).build()

    asgi_app = cast(ASGIApp, fastapi_app)
    transport = ASGITransport(app=asgi_app)
    http_client = httpx.AsyncClient(transport=transport, base_url="http://hh-bot-internal")
    application.bot_data["_api_httpx_client"] = http_client

    backend_api = BackendApi(http_client)
    register_handlers(application, backend_api)

    commands = [
        BotCommand("start", "Онбординг и главное меню"),
        BotCommand("campaign", "Запустить кампанию"),
        BotCommand("quota", "Показать квоту"),
        BotCommand("plans", "Планы и оплата"),
    ]
    application.bot_data["__commands__"] = commands

    application.post_shutdown = _close_api_client
    return application
