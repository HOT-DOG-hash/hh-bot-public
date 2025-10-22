# PAYMENT_SCHEMA_SPEC

Цель: привести схему БД к ожиданиям ORM и бизнес-логики холста HH-bot (устойчивые платежи с идемпотентностью, дедуп вебхуков и ретраями).

## Общие требования
- Новые таблицы используют UUID (gen_random_uuid()) как PK.
- Дата/время — TIMESTAMPTZ с default current_timestamp.
- FK и каскадные действия:
  • payments.user_id → users.id (ON DELETE CASCADE)
  • payments.subscription_id → subscriptions.id (ON DELETE SET NULL)
  • payments.plan_code → plans.code (ON DELETE RESTRICT)
  • payment_events.payment_id → payments.id (ON DELETE SET NULL)
  • payment_attempts.payment_id → payments.id (ON DELETE CASCADE)
- Индексы под бизнес-кейсы (по пользователю, статусу, платежу).
- SQLite: ENUM сохраняются как TEXT через SAEnum(..., native_enum=False), JSON через JSON().

## Таблица payments (новое состояние)
- id UUID PK (default gen_random_uuid())
- user_id FK на users.id (CASCADE)
- subscription_id FK на subscriptions.id (SET NULL)
- plan_code FK на plans.code (RESTRICT)
- provider ENUM provider_enum
- provider_payment_id TEXT, UNIQUE
- idempotency_key TEXT, UNIQUE (идемпотентность initiate_payment)
- amount_minor INT NOT NULL
- currency TEXT(3) NOT NULL default 'RUB'
- status ENUM payment_status_enum
- confirmation_url TEXT NULL
- raw JSONB NULL
- created_at TIMESTAMPTZ default now()
- updated_at TIMESTAMPTZ default now(), on update now()

Индексы: ix_payments_user_created (user_id, created_at); ix_payments_status_created (status, created_at).

## Таблица payment_events
- id UUID PK
- payment_id UUID NULL, FK на payments (SET NULL)
- provider_event_id TEXT UNIQUE
- event_type ENUM payment_event_type_enum (см. холст YooMoney)
- payload JSONB
- created_at TIMESTAMPTZ default now()

Индекс: ix_payment_events_payment_created (payment_id, created_at).

## Таблица payment_attempts
- id UUID PK
- payment_id UUID NOT NULL, FK на payments (CASCADE)
- phase ENUM payment_attempt_phase_enum (init, provider_call, webhook, retry, final)
- attempt_no INT NOT NULL (порядковый счётчик внутри фазы)
- provider ENUM provider_enum
- ok BOOLEAN default false
- error_code TEXT NULL
- error_message TEXT NULL
- duration_ms INT NOT NULL
- next_retry_at TIMESTAMPTZ NULL
- idempotency_key TEXT UNIQUE NULL (фиксируем ключ внешнего вызова)
- created_at TIMESTAMPTZ default now()
- updated_at TIMESTAMPTZ default now(), on update now()

Ограничения: UNIQUE (payment_id, phase, attempt_no). Индексы: ix_payment_attempts_payment_phase (payment_id, phase); ix_payment_attempts_phase_updated (phase, updated_at).

## ENUM-типов
- provider_enum: yoomoney (позже можно расширить).
- payment_status_enum: pending, succeeded, canceled, expired, failed.
- payment_event_type_enum: payment.waiting_for_capture, payment.succeeded, payment.canceled, payment.failed (приводим к холсту).
- payment_attempt_phase_enum: init, provider_call, webhook, retry, final.

## Инварианты и бизнес-правила
- Идемпотентность payments через уникальный idempotency_key и повторное чтение в initiate_payment.
- Дедуп вебхуков через provider_event_id.
- Ретраи: каждая попытка фиксируется в payment_attempts, поле next_retry_at хранит плановый ретрай (10/30/60 минут согласно холсту).
- Audit trail: payment_events хранит весь поток событий, даже при удалении платежа (SET NULL).
- Дополнительные поля (plan_code, subscription_id) обеспечивают связку с тарифами и подписками.
