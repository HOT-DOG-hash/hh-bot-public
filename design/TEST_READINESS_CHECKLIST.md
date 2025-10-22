# TEST_READINESS_CHECKLIST — миграции платежей

## Локально
- [ ] SQLite: Base.metadata.create_all() на in-memory базе (убедиться, что новые таблицы создаются, ENUM мапится на TEXT).
- [ ] Postgres dev: ./scripts/smoke_alembic.sh (двойной цикл down→up→down→up).
- [ ] Ручной alembic downgrade/upgrade на локальном контейнере.

## На дампе
- [ ] Восстановить свежий pg_dump в отдельную БД.
- [ ] Применить ревизии (expand + migrate) → прогнать smoke.
- [ ] Выполнить backfill-скрипты; сравнить количество строк и уникальные ключи.
- [ ] Заснять контрольные выборки (N пользователей, статистика попыток).

## В CI
- [ ] Workflow unit-sqlite: lint, mypy, smoke, pytest -m "not pg".
- [ ] Workflow pg-integration (nightly): smoke, pytest -m pg (с фикстурой Postgres).
- [ ] Публиковать артефакты: лог smoke, отчёт backfill.

## Мониторинг после релиза
- [ ] Метрики: количество платежей без idempotency_key, дубликаты provider_event_id.
- [ ] Алерты: spike failed/expired > X%, webhook duplicates > threshold.
- [ ] Логи: PaymentAttempt phase, время retry.
