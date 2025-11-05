# экспортируем ПАКЕТЫ, внутри которых есть переменная `router`
from . import admin_api, auto_campaigns, bot_api

__all__ = ["bot_api", "admin_api", "auto_campaigns"]
