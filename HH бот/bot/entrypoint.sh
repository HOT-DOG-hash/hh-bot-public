#!/usr/bin/env bash
set -euo pipefail

cd /app

# .env (CRLF→LF + export)
if [ -f "/app/.env" ]; then
  sed -i 's/\r$//' /app/.env
  set -a; . /app/.env; set +a
fi

# подстраховка: если переменная не пришла из compose — зададим дефолт
export PYTHONPATH="${PYTHONPATH:-/app:/app/HH бот}"

# гарантируем запуск бота
export ENABLE_TELEGRAM_BOT=1

# явный раннер, чтобы healthcheck находил процесс
exec python "/app/HH бот/bot/runner.py"
