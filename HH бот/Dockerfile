# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 \
    build-essential gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ["HH бот/bot/entrypoint.sh", "/bot/entrypoint.sh"]
RUN chmod +x /bot/entrypoint.sh

COPY . /app
ENV PYTHONPATH="/app/HH бот:${PYTHONPATH}"

RUN apt-get purge -y --auto-remove build-essential gcc libpq-dev || true