# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# системные зависимости для psycopg/asyncpg + procps (pgrep/ps для healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 build-essential gcc libpq-dev procps \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# код приложения
COPY . /app

# entrypoint бота (учёт пробелов/кириллицы в пути)
RUN chmod +x "/app/HH бот/bot/entrypoint.sh" || true

# очистка dev-пакетов, оставляем libpq5 и procps
RUN apt-get purge -y --auto-remove build-essential gcc libpq-dev || true \
 && rm -rf /var/lib/apt/lists/*

# non-root
RUN groupadd -r app && useradd -r -g app -m app \
 && mkdir -p /var/log/app && chown -R app:app /app /var/log/app
USER app

# -------- web --------
FROM base AS web
ENV APP_MODULE=backend.app.main:app WEB_PORT=8000
EXPOSE 8000
CMD ["sh","-lc","python -m uvicorn $APP_MODULE --host 0.0.0.0 --port $WEB_PORT"]

# -------- bot --------
FROM base AS bot
ENTRYPOINT ["/bin/bash","-lc","exec \"/app/HH бот/bot/entrypoint.sh\""]
