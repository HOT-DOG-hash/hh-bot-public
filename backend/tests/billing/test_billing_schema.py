from __future__ import annotations

import importlib
import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import IntegrityError


def _create_database(base_url: URL) -> URL:
    db_name = f"billing_test_{uuid.uuid4().hex}"
    admin = base_url.set(database="postgres")
    engine = create_engine(admin)
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    engine.dispose()
    return base_url.set(database=db_name)


def _drop_database(base_url: URL, db_name: str) -> None:
    admin = base_url.set(database="postgres")
    engine = create_engine(admin)
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
    engine.dispose()


def _create_test_user(conn) -> int:
    result = conn.execute(
        text(
            """
            INSERT INTO users (tg_id, is_active, last_activity, created_at, updated_at)
            VALUES (:tg_id, true, NOW(), NOW(), NOW())
            RETURNING id
            """
        ),
        {"tg_id": f"test-{uuid.uuid4().hex}"},
    )
    return result.scalar_one()


@pytest.fixture()
def migrated_engine(monkeypatch):
    raw_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://dev:dev@db:5432/hhbot")
    base_url = make_url(raw_url)
    test_url = _create_database(base_url)

    for key, value in {
        "DATABASE_URL": str(test_url),
        "SECRET_KEY": "test-secret",
        "ADMIN_USER": "test-admin",
        "ADMIN_PASS": "test-pass",
        "ADMIN_SECRET_TOKEN": "test-admin-token",
        "YOOMONEY_TOKEN": "test-yoomoney-token",
        "TELEGRAM_BOT_TOKEN": "test-telegram-token",
        "CF_TUNNEL_TOKEN": "test-cf-token",
    }.items():
        monkeypatch.setenv(key, value)

    import backend.app.core.config as config_module

    importlib.reload(config_module)

    alembic_cfg = Config(str(Path("alembic.ini")))
    alembic_cfg.set_main_option("sqlalchemy.url", str(test_url))
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(test_url)
    try:
        yield engine
    finally:
        command.downgrade(alembic_cfg, "base")
        engine.dispose()
        _drop_database(base_url, test_url.database)


def test_seed_plans(migrated_engine):
    with migrated_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT code, period, amount_minor, granted_quota, non_renewable FROM plans ORDER BY code"
            )
        ).fetchall()
    expected = {
        ("FREE_TRIAL", "trial", 0, 10, True),
        ("WEEKLY", "week", 69000, 0, False),
        ("MONTHLY", "month", 190000, 0, False),
    }
    assert set(rows) == expected


def test_free_trial_unique(migrated_engine):
    with migrated_engine.begin() as conn:
        user_id = _create_test_user(conn)
        conn.execute(
            text(
                """
                INSERT INTO application_quotas (
                    id, user_id, plan_code, granted, consumed, non_renewable, activated_at
                ) VALUES (:id, :user_id, 'FREE_TRIAL', 10, 0, true, NOW())
                """
            ),
            {"id": uuid.uuid4(), "user_id": user_id},
        )
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO application_quotas (
                        id, user_id, plan_code, granted, consumed, non_renewable, activated_at
                    ) VALUES (:id, :user_id, 'FREE_TRIAL', 10, 0, true, NOW())
                    """
                ),
                {"id": uuid.uuid4(), "user_id": user_id},
            )


def test_quota_consumed_check(migrated_engine):
    with migrated_engine.begin() as conn:
        user_id = _create_test_user(conn)
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO application_quotas (
                        id, user_id, plan_code, granted, consumed, non_renewable, activated_at
                    ) VALUES (:id, :user_id, 'WEEKLY', 5, 6, false, NOW())
                    """
                ),
                {"id": uuid.uuid4(), "user_id": user_id},
            )


def test_payment_uniqueness(migrated_engine):
    subscription_id = uuid.uuid4()
    with migrated_engine.begin() as conn:
        user_id = _create_test_user(conn)
        conn.execute(
            text(
                """
                INSERT INTO subscriptions (
                    id, user_id, plan_code, status, current_period_start, current_period_end,
                    next_charge_at, cancel_at, cancel_at_period_end
                ) VALUES (
                    :id, :user_id, 'WEEKLY', 'active', NOW(), NOW() + interval '7 days',
                    NOW() + interval '7 days', NULL, false
                )
                """
            ),
            {"id": subscription_id, "user_id": user_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO payments (
                    id, user_id, subscription_id, plan_code, provider, provider_payment_id,
                    idempotency_key, amount_minor, currency, status
                ) VALUES (
                    :id, :user_id, :subscription_id, 'WEEKLY', 'yoomoney', 'ext-1',
                    'idem-1', 69000, 'RUB', 'pending'
                )
                """
            ),
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "subscription_id": subscription_id,
            },
        )
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO payments (
                        id, user_id, subscription_id, plan_code, provider, provider_payment_id,
                        idempotency_key, amount_minor, currency, status
                    ) VALUES (
                        :id, :user_id, :subscription_id, 'WEEKLY', 'yoomoney', 'ext-2',
                        'idem-1', 69000, 'RUB', 'pending'
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                },
            )
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO payments (
                        id, user_id, subscription_id, plan_code, provider, provider_payment_id,
                        idempotency_key, amount_minor, currency, status
                    ) VALUES (
                        :id, :user_id, :subscription_id, 'WEEKLY', 'yoomoney', 'ext-1',
                        'idem-2', 69000, 'RUB', 'pending'
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                },
            )
pytestmark = pytest.mark.pg
