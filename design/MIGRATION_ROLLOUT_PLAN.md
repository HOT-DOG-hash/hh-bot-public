# MIGRATION_ROLLOUT_PLAN — платежный контур

## Цели
1. Расширить схему без простоя (expand).
2. Перенести/синхронизировать данные (migrate).
3. Завершить и убрать временные артефакты (contract).

## Предпосылки
- Перед началом: pg_dump прод, dry-run на staging.
- Код остаётся старым до завершения цикла, поэтому новые объекты должны быть совместимыми.

## Expand
1. Создать ENUM-типы через idempotent DO-block (provider_enum, payment_status_enum, payment_event_type_enum, payment_attempt_phase_enum).
2. ALTER TABLE payments: добавить новые колонки (subscription_id, plan_code, idempotency_key, amount_minor, raw JSONB, confirmation_url, updated_at TIMESTAMPTZ) и новые индексы.
3. Создать таблицу payment_events (UUID PK, FK на payments SET NULL) + индексы + уникальный provider_event_id.
4. Создать таблицу payment_attempts (UUID PK, FK на payments CASCADE) + индексы + unique idempotency_key.
5. При необходимости завести временные триггеры/dual-write (amount → amount_minor и т. п.).

## Migrate
1. Бэкфилл payments: amount → amount_minor, сформировать idempotency_key (если отсутствует — combine provider/payment id), заполнить plan_code и subscription_id.
2. Бэкфилл payment_events: импорт исторических вебхуков (если хранятся в логах). В противном случае — зафиксировать, что история отсутствует.
3. Бэкфилл payment_attempts: по каждому платежу добавить запись phase=legacy с attempt_no=1, либо восстановить из логов provider.
4. Включить фичефлаг dual-write в сервисах: новые записи пишутся и в старые, и в новые поля.
5. После проверки (метрики, QA) переключить чтение на новые поля.

## Contract
1. Удалить временные триггеры/dual-write.
2. Удалить устаревшие ограничения (например unique(provider, external_id)).
3. Финальный cleanup: drop legacy колонок и индексов, если они не используются.

## Откат
- После expand: alembic downgrade до старых ревизий → удалить новые таблицы (данных ещё нет).
- После migrate: откат = restore pg_dump + повторное применение старых ревизий.
- После contract: re-apply предыдущие ревизии, вернуть ограничения.

## Контроль
- Smoke на staging (down→up→down→up) перед каждой фазой.
- Метрики миграции: количество платежей без idempotency_key, количество дублей provider_event_id.
