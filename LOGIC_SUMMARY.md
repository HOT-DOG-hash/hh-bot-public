# LOGIC_SUMMARY — схема ↔ продуктовая логика

## Тарифы и планы
- Миграция: backend/migrations/versions/p0_3_billing_schema.py (таблицы plans, subscriptions, application_quotas, сиды FREE_TRIAL, WEEKLY 690 ₽, MONTHLY 1900 ₽).
- ORM: backend/app/models/billing.py (Plan, Subscription, ApplicationQuota, UserApplication). Partial-индекс триала реализован только в миграции (Postgres).

## FSM платежей и подписок
- Сервис: backend/app/services/payments.py — состояния YooMoney мапятся в pending|succeeded|canceled|expired|failed; успешный вебхук активирует подписку.
- Подписки: backend/app/services/billing.py::activate_subscription продлевает valid_until и выставляет active=True.
- Метрики: backend/app/core/metrics.py (счётчики инициирования/статусов/вебхуков, гистограммы latency).

## Квоты и отклики
- Триал и списания: backend/app/routers/apply.py (_consume_trial_quota, _record_application).
- Business-guard: backend/app/services/billing_guard.py — режимы paid|trial|none.
- Таблица откликов: уникальность user_id + vacancy_id (модель UserApplication).

## Реферальная программа
- GAP: в коде отсутствуют сущности и миграции для рефералок — требуется проектирование.

## Админка / API / наблюдаемость
- Админские ручки: backend/app/routers/admin.py и backend/app/routers/admin_api/*.
- CI: .github/workflows/ci.yml — lint → mypy → smoke → pytest -m "not pg"; nightly PG-интеграция.
- Логирование/метрики: backend/app/core/logging.py (structlog), backend/app/core/metrics.py (in-memory, экспорт отсутствует).

## Чек-лист релизной готовности
- [x] Smoke Alembic (двойной цикл, динамический порт) — scripts/smoke_alembic.sh.
- [ ] ORM ⇄ миграции согласованы (autogenerate чистый) — требуется доработка.
- [ ] Тестовая матрица (pytest -m "not pg", pytest -m pg) — не настроена.
- [ ] Реферальный функционал — отсутствует.
- [ ] Экспорт метрик/алертов (Prometheus/Grafana) — отсутствует.
- [ ] Документация по оплатам/возвратам/рефералке — требуется.

## План миграции
- Спецификация и rollout-план для payment_events и payment_attempts оформлены в каталоге design/.

