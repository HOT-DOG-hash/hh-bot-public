# HH бот/backend/app/config.py
import os
from dotenv import load_dotenv

# Подхват .env, если есть
load_dotenv()

# Телеграм токен (можно задать либо TELEGRAM_BOT_TOKEN, либо BOT_TOKEN)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""

# Необязательно: порт и путь логов (используются в проекте по окружению)
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
BOT_LOG_FILE = os.getenv("BOT_LOG_FILE", "/var/log/app/bot.log")
