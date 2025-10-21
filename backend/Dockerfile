FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# curl нужен для healthcheck из docker-compose
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей (покрываем оба варианта расположения requirements)
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt || true
COPY backend/requirements.txt /app/backend-requirements.txt
RUN if [ -f /app/backend-requirements.txt ]; then pip install -r /app/backend-requirements.txt; fi

# Копируем код (ожидаем, что backend-код лежит в app/)
COPY app/ /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
