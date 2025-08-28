# Dockerfile для HH бота (front_bot)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/bot

WORKDIR /bot

# База
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

# Логи
RUN mkdir -p /var/log/app

# Сначала зависимости (кэш)
COPY requirements*.txt /bot/
RUN python -m pip install --no-cache-dir -r /bot/requirements.txt

# Затем код
COPY . /bot/

# Лечим CRLF + BOM и делаем исполняемым
RUN sed -i 's/\r$//' /bot/entrypoint.sh \
 && sed -i '1s/^\xEF\xBB\xBF//' /bot/entrypoint.sh \
 && chmod +x /bot/entrypoint.sh

STOPSIGNAL SIGINT
ENTRYPOINT ["/bin/sh", "/bot/entrypoint.sh"]
