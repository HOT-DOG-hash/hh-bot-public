# migrations/env.py
import sys
import pathlib
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# 1) Добавляем путь до backend, чтобы импорты app.* работали
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # .../backend
sys.path.append(str(BASE_DIR))

# 2) Тянем настройки и метаданные моделей
from app.core.config import settings
from app.models import Base

# --- Alembic config ---
config = context.config

# 2) Единый источник правды для строки подключения — .env (Settings)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей — для автогенерации
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Общая конфигурация контекста миграций (общая для sync/async)."""

    # 5) Для SQLite включаем batch-режим (иначе ALTER-операции будут падать)
    url = config.get_main_option("sqlalchemy.url") or ""
    is_sqlite = url.startswith("sqlite")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,            # 4) Отслеживать изменения типов колонок
        render_as_batch=is_sqlite,    # 5) Нужен для SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в online-режиме (с асинхронным движком)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Важно: все sync-операции выполняем через run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # 3) Асинхронный запуск
    asyncio.run(run_migrations_online())
