# DEV_CHANGELOG

## 2025-10-24 — P0.1 Baseline Checks
- восстановлен scripts/dev_check.sh с запуском uff, mypy, pytest -m "not pg".
- настроены динамические пути для смешанной структуры ackend/HH бот/backend.

## 2025-10-24 — P0.1 Пакеты и типизация
- обновлены зависимости (pydantic 2.9.2, syncpg 0.30.0, добавлены mypy, uff, типы aiofiles).
- добавлен pyproject.toml с конфигурацией uff, mypy, pytest.
- приведены импорты к пространству ackend.app.*, исправлены модели, миграции и вспомогательные скрипты под строгий mypy.
- поправлены тесты health и esumes исходя из фактических эндпоинтов.

## 2025-10-25 — P0.2 Database migrations & seeds
- Добавлены модели и миграции p0_3/p1_0/p1_1 для биллинга с FK, enum и сидом тарифов (FREE_TRIAL, WEEKLY, MONTHLY) согласно PAYMENT_SCHEMA_SPEC.
- Протестирован полный цикл Alembic (downgrade base → upgrade head) и автоген на SQLite (отмечено ограничение по FK).
- Обновлён seed_dev.py: наполняет планы и базового пользователя; проверено на sqlite+aiosqlite.
- Реализован эндпойнт `/admin/plans` и тест `backend/tests/billing/test_billing_schema.py`, проверяющий сиды через API.
- Описана схема в design/PAYMENT_SCHEMA_SPEC.md для сверки миграций и API.

## 2025-10-25 — P0.3 Payments FSM & YooMoney webhook
- Реализованы сервисы billing/analytics с idempotency, FSM-обновлением платежей и подписок.
- Добавлены эндпоинты `/api/v1/payments/initiate`, `/api/v1/payments/webhook`, поддержка Prometheus (`/metrics`).
- Настроены события аналитики и счётчики `payments_*`, `webhook_lag_seconds`.
- Покрыты тестами: `test_yoomoney_resilience.py`, `test_yoomoney_webhook.py`.

## 2025-10-26 — P0.4 Telegram onboarding & billing API
- Добавлены публичные эндпоинты `/api/v1/billing/*`, `/api/v1/quota` с активацией FREE_TRIAL и продлением подписки.
- Восстановлен бот-фронт: мини-лендинг `/start`, FSM 10 шагов, привязка к REST через httpx+ASGITransport, обработчики `/campaign`, `/plans`, `/quota`.
- Активация YooMoney: кнопки оплатить тариф → `/payments/initiate`, CTA при исчерпании квоты, сообщения об остатке триала (10 откликов).
- Написаны тесты `tests/billing/test_public_billing.py` и `tests/quota/test_quota_endpoints.py`, документация обновлена.
