from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    CANCELED = "canceled"


class Subscription(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_code: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("plans.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
    )
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_charge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    payments: Mapped[list["Payment"]] = relationship(back_populates="subscription")


from backend.app.models.user import User  # noqa: E402
from backend.app.models.payments import Payment  # noqa: E402
