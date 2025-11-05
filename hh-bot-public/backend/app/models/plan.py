from __future__ import annotations

from decimal import Decimal
from sqlalchemy import Boolean, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from backend.app.models.base import Base, TimestampMixin


class Plan(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    duration_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    granted_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
