# MIGRATION_GAP_REPORT — платежный контур

## Сводка несоответствий

Ожидается (ORM/сервисы | холст) → что есть в базе сейчас → риск/критичность.

1. Таблица 'payment_events' (UUID PK, FK на payments, уникальный provider_event_id, JSON payload, индексы по (payment_id, created_at)) — в схеме отсутствует. Риск: невозможно дедуплицировать вебхуки, нет audit trail, relationship Payment.events ломается. Критичность: P0.
2. Таблица 'payment_attempts' (UUID PK, FK на payments ON CASCADE, уникальность (payment_id, phase, attempt_no), хранение ретраев и ошибок) — отсутствует. Риск: _record_attempt пишет в никуда, история попыток теряется, FSM ретраев невозможен. Критичность: P0.
3. Таблица 'payments' в ORM ожидает UUID PK, поля subscription_id, plan_code, idempotency_key, amount_minor, raw, confirmation_url, индексы (user_id, created_at) и (status, created_at), уникальность idempotency_key и provider_payment_id. В ревизии 20251020_0001_core_tables: INT PK, нет FK на subscriptions/plans, отсутствуют перечисленные поля, уникальность (provider, external_id), индексы только по user_id и status. Риск: несовместимость со слоем ORM и идемпотентностью. Критичность: P0.
4. ENUMы payment_status, provider, статусы events/attempts — отсутствуют, используются свободные VARCHAR. Риск: FSM не контролируется. Критичность: P1.
5. Уникальный provider_event_id (dedup вебхуков) и уникальный idempotency_key в payments — отсутствуют. Риск: повторная обработка вебхуков и нарушение идемпотентности. Критичность: P0.
6. Колонка confirmation_url (используется сервисом) — отсутствует. Риск: URL не сохраняется. Критичность: P1.
7. Производственные индексы по created_at — частично, нет композитных (user_id, created_at) и (status, created_at). Риск: производительность аналитики (P2).

## Детализация по таблицам

### payments
- ORM (backend/app/models/payments.py): UUID PK (через UUIDType), FK на users/subscriptions/plans, поля plan_code, subscription_id, idempotency_key, raw, confirmation_url; индексы ix_payments_user_created, ix_payments_status_created; уникальные ключи idempotency_key и provider_payment_id.
- Миграция 20251020_0001_core_tables: INT PK, отсутствуют FK на subscriptions и plans, отсутствуют поля plan_code, subscription_id, idempotency_key, raw, confirmation_url. Уникальность (provider, external_id), индексы по user_id и status.

### payment_events
- Ожидаемая модель: UUID PK, FK на payments (delete set null), provider_event_id UNIQUE, event_type по FSM холста (например payment.succeeded, payment.canceled, payment.pending, payment.failed), payload JSONB, created_at TIMESTAMPTZ, индекс (payment_id, created_at).
- В текущей схеме: таблица отсутствует.

### payment_attempts
- Ожидаемая модель: UUID PK, FK на payments (cascade), attempt_no, phase (init/provider/webhook ...), ok, error, duration_ms, created_at, UNIQUE (payment_id, phase, attempt_no), индекс (payment_id, phase).
- В текущей схеме: таблица отсутствует.

### ENUMы
- Используются перечисления PaymentStatus (pending, succeeded, canceled, expired, failed) и Provider (yoomoney). Холст добавляет статусные множества для events/attempts. В Postgres потребуются настоящие ENUM с idempotent DO blocks; в SQLite — хранение как TEXT.

## Критичность/приоритет
- P0: отсутствие payment_events, payment_attempts, idempotency_key, уникальных ключей.
- P1: отсутствие ENUM, confirmation_url, индексных оптимизаций.
- P2: дополнительные индексы по created_at.
