from __future__ import annotations

from telegram.ext import Application

from front_bot.api import BackendApi
from front_bot.routers import start


def register_handlers(application: Application, api: BackendApi) -> None:
    """
    Attach all Telegram handlers required for the MVP bot.
    """
    start.register(application, api)


__all__ = ["register_handlers"]
