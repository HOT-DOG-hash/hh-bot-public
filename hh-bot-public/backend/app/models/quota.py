from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class UserTrial(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "users_trials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    plan_code: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("plans.code", ondelete="RESTRICT"),
        nullable=False,
    )
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumed_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="trials")


class ApplicationQuota(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "application_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    plan_code: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("plans.code", ondelete="SET NULL"),
        nullable=True,
    )
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    daily_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trial_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trial_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="quotas")


if TYPE_CHECKING:
    from backend.app.models.user import User
