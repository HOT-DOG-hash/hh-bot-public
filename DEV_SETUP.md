# Dev/Test Setup Snapshot

## Инструменты
- Python: команда python3 -V (текущее значение 3.12.3)
- uv: команда uv --version (текущее значение 0.9.4)
- Docker ≥ 24 (для временного Postgres)

## Установка зависимостей
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt

## Alembic smoke (Postgres 16)
./scripts/smoke_alembic.sh
Скрипт поднимает контейнер на свободном порту, выполняет два цикла downgrade base → upgrade head и удаляет контейнер.

## Тесты
Пока нет единой матрицы SQLite/Postgres. Фактический статус:
- pytest -m "not pg" — ⚠️ маркеров и фикстур ещё нет (исторические тесты ожидают Postgres).
- pytest -m pg — ⚠️ требует PG-фикстур и актуализации тестов.

## TODO
- Восстановить соответствие ORM↔миграции (alembic autogenerate даёт диффы).
- Разнести тесты по SQLite/PG и настроить фикстуры.
- Привести pytest к зелёному состоянию.
- Снять технический долг по проверкам (LOGIC_SUMMARY.md, релизный чек-лист).
