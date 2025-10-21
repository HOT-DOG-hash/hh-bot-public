from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDType

if TYPE_CHECKING:
    from .payments import Payment


class PlanPeriod(str, Enum):
    TRIAL = "trial"
    WEEK = "week"
    MONTH = "month"


class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    period: Mapped[PlanPeriod] = mapped_column(
        SAEnum(PlanPeriod, name="plan_period_enum", native_enum=False), nullable=False
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    currency: Mapped[str] = mapped_column(
        String(length=3), nullable=False, server_default=text("'RUB'")
    )
    granted_quota: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    non_renewable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_product_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    subscriptions: Mapped[list[Subscription]] = relationship("Subscription", back_populates="plan")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="plan")
    quotas: Mapped[list[ApplicationQuota]] = relationship("ApplicationQuota", back_populates="plan")

    __table_args__ = (
        Index("ix_plans_period", "period"),
        Index("ix_plans_is_recurring", "is_recurring"),
    )


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_code: Mapped[str] = mapped_column(
        ForeignKey("plans.code", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status_enum", native_enum=False),
        nullable=False,
    )
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_charge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    plan: Mapped[Plan] = relationship(back_populates="subscriptions")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="subscription")

    __table_args__ = (
        Index("ix_subscriptions_user_status", "user_id", "status"),
        Index("ix_subscriptions_user_next_charge", "user_id", "next_charge_at"),
    )


class ApplicationQuota(Base, TimestampMixin):
    __tablename__ = "application_quotas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_code: Mapped[str] = mapped_column(
        ForeignKey("plans.code", ondelete="RESTRICT"), nullable=False
    )
    granted: Mapped[int] = mapped_column(Integer, nullable=False)
    consumed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    non_renewable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exhausted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped[Plan] = relationship(back_populates="quotas")

    __table_args__ = (
        CheckConstraint(
            "consumed >= 0 AND consumed <= granted",
            name="ck_application_quotas_consumed_range",
        ),
        Index(
            "uq_application_quotas_trial_once_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("plan_code = 'FREE_TRIAL'"),
        ),
        Index("ix_application_quotas_exhausted", "exhausted_at"),
    )


class UserApplication(Base):
    __tablename__ = "user_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "vacancy_id", name="uq_user_applications_user_vacancy"),
        Index("ix_user_applications_created_at", "created_at"),
    )


__all__ = [
    "ApplicationQuota",
    "Plan",
    "PlanPeriod",
    "Subscription",
    "SubscriptionStatus",
    "UserApplication",
]
