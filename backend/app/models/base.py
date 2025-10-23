from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, MetaData, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

try:  # pragma: no cover - optional Postgres extras
    from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB  # type: ignore
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID  # type: ignore
except ImportError:  # pragma: no cover
    PostgresJSONB = None  # type: ignore[assignment]
    PostgresUUID = None  # type: ignore[assignment]


class JSONBType(TypeDecorator):
    """Postgres JSONB with transparent fallback to generic JSON."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if PostgresJSONB is not None and dialect.name in {"postgresql", "postgres", "psycopg"}:
            return dialect.type_descriptor(PostgresJSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


JSONB = JSONBType()


class UUIDType(TypeDecorator):
    """UUID that stores native UUIDs on Postgres and strings elsewhere."""

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if PostgresUUID is not None and dialect.name in {"postgresql", "postgres", "psycopg"}:
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value: Any, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )


__all__ = [
    "Base",
    "JSONB",
    "JSONBType",
    "TimestampMixin",
    "UUIDType",
]
