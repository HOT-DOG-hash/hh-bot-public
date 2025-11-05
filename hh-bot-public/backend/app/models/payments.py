from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class Provider(str, enum.Enum):
    YOOMONEY = "yoomoney"


class PaymentStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    EXPIRED = "expired"


class Payment(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "payments"

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
    provider: Mapped[Provider] = mapped_column(
        Enum(Provider, name="payment_provider"),
        nullable=False,
        default=Provider.YOOMONEY,
    )
    payment_method_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("payment_methods.id", ondelete="SET NULL"),
        nullable=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.INITIATED,
    )
    invoice_pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="payments")
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="payments")
    method: Mapped[Optional["PaymentMethod"]] = relationship(back_populates="payments")
    attempts: Mapped[list["PaymentAttempt"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events: Mapped[list["PaymentEvent"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PaymentMethod(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "payment_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[Provider] = mapped_column(
        Enum(Provider, name="payment_method_provider"),
        nullable=False,
        default=Provider.YOOMONEY,
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    masked_pan: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="payment_methods")
    payments: Mapped[list["Payment"]] = relationship(back_populates="method")


class PaymentAttempt(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "payment_attempts"

    __table_args__ = (
        UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_idx"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[Provider] = mapped_column(
        Enum(Provider, name="payment_attempt_provider"),
        nullable=False,
        default=Provider.YOOMONEY,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_attempt_status"),
        nullable=False,
        default=PaymentStatus.INITIATED,
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    payment: Mapped["Payment"] = relationship(back_populates="attempts")


class PaymentEvent(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "payment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_event_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    payment: Mapped["Payment"] = relationship(back_populates="events")


from backend.app.models.subscription import Subscription  # noqa: E402
from backend.app.models.user import User  # noqa: E402
