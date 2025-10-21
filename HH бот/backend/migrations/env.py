# migrations/env.py
import asyncio
import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# 1) Добавляем путь до backend, чтобы импорты app.* работали
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # .../backend
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# 2) Тянем настройки и метаданные моделей
from app.core.config import settings
from app.models import Base  # убедись, что Base доступен через app/models/__init__.py

# --- Alembic config ---
config = context.config

# 3) Единый источник правды для строки подключения — ENV
db_url = settings.database_url
if not db_url:
    raise RuntimeError("DATABASE_URL is not set; Alembic cannot run.")
config.set_main_option("sqlalchemy.url", db_url)

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей — для автогенерации
target_metadata = Base.metadata


def run_migrations_offline() -> None:
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
    # Для SQLite включаем batch-режим
    url = config.get_main_option("sqlalchemy.url") or ""
    is_sqlite = url.startswith("sqlite")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=is_sqlite,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
