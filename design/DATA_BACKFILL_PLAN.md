# DATA_BACKFILL_PLAN — платежный контур

## Цели
- Конвертировать существующие записи payments в новую схему (amount_minor, idempotency_key, связи с тарифами).
- При необходимости восстановить события и попытки (events/attempts) из логов.

## Источники данных
1. Текущая таблица payments (INT PK, amount, external_id, payload_json).
2. Логи провайдера YooMoney (для вебхуков).
3. Сервисные логи приложения (track_event, analytics) — как fallback.

## Шаги backfill
1. Подготовка: pg_dump прод → восстановление на staging → включение новых миграций.
2. Payments:
   - amount_minor = amount * 100.
   - idempotency_key: если отсутствует, сформировать hash(provider, external_id, created_at).
   - plan_code: брать из payload_json либо подставлять дефолт (MONTHLY).
   - subscription_id: искать последнюю активную подписку пользователя, иначе NULL.
   - raw = payload_json (без изменений).
3. Payment events:
   - Если вебхуки сохранены в audit_logs — перенести данные (provider_event_id = hash по исходному event id).
   - Если истории нет — создать одиночное событие event_type=legacy на created_at платежа (для соблюдения целостности).
4. Payment attempts:
   - При наличии логов provider — восстановить реальные попытки (phase по типу события, duration_ms по логам).
   - Если данных нет — создать одну попытку phase=legacy, attempt_no=1, ok = (status in succeeded/canceled), error_code = NULL.
5. Валидация:
   - Сверка количества строк.
   - Проверка уникальности idempotency_key и provider_event_id.
   - Случайная ручная выборка (N пользователей) со сверкой метрик.

## Инструменты
- SQL скрипты или батчевые задания (LIMIT + ORDER BY created_at).
- После обновлений — ANALYZE, фиксация метрик (количество платежей без idempotency_key и events).

## Откат
- Работать на копии до подтверждения.
- Для прод: перед апдейтом — snapshot таблиц (CREATE TABLE backup AS SELECT ...).
