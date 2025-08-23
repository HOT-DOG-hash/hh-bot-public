# экспортируем ПАКЕТЫ, внутри которых есть переменная `router`
from . import bot_api, admin_api

__all__ = ["bot_api", "admin_api"]
