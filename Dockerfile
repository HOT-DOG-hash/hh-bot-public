FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# системные зависимости (для asyncpg, psycopg, и т.п.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 build-essential gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# entrypoint бота
COPY ["HH бот/bot/entrypoint.sh", "/bot/entrypoint.sh"]
RUN chmod +x /bot/entrypoint.sh

# код приложения
COPY . /app

# облегчение итогового образа
RUN apt-get purge -y --auto-remove build-essential gcc libpq-dev || true

# Команды/entrypoint задаются в docker-compose (разные для web и bot)
