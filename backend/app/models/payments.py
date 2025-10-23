from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
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

from .base import JSONB, Base, TimestampMixin, UUIDType

if TYPE_CHECKING:
    from .billing import Plan, Subscription
    from .core import User



class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    EXPIRED = "expired"
    FAILED = "failed"


class PaymentEventType(str, Enum):
    WAITING_FOR_CAPTURE = "payment.waiting_for_capture"
    PENDING = "payment.pending"
    SUCCEEDED = "payment.succeeded"
    CANCELED = "payment.canceled"
    FAILED = "payment.failed"


class PaymentAttemptPhase(str, Enum):
    INIT = "init"
    PROVIDER_CALL = "provider_call"
    WEBHOOK = "webhook"
    RETRY = "retry"
    FINAL = "final"


class Provider(str, Enum):
    YOOMONEY = "yoomoney"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    plan_code: Mapped[str] = mapped_column(
        ForeignKey("plans.code", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[Provider] = mapped_column(
        SAEnum(Provider, name="provider_enum", native_enum=False), nullable=False
    )
    provider_payment_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(length=3), nullable=False, server_default=text("'RUB'")
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum", native_enum=False), nullable=False
    )
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="payments")
    plan: Mapped[Plan] = relationship("Plan", back_populates="payments")
    subscription: Mapped[Subscription | None] = relationship(
        "Subscription", back_populates="payments"
    )
    events: Mapped[list[PaymentEvent]] = relationship(
        "PaymentEvent", back_populates="payment", cascade="all, delete-orphan"
    )
    attempts: Mapped[list[PaymentAttempt]] = relationship(
        "PaymentAttempt", back_populates="payment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("provider_payment_id", name="uq_payments_provider_payment_id"),
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
        Index("ix_payments_user_created", "user_id", "created_at"),
        Index("ix_payments_status_created", "status", "created_at"),
    )


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    __table_args__ = (
        UniqueConstraint("provider_event_id", name="uq_payment_events_provider_event_id"),
        Index("ix_payment_events_payment_created", "payment_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provider_event_id: Mapped[str] = mapped_column(String(length=128), nullable=False)
    event_type: Mapped[PaymentEventType] = mapped_column(
        SAEnum(PaymentEventType, name="payment_event_type_enum", native_enum=False),
        nullable=False,
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    payment: Mapped[Payment | None] = relationship("Payment", back_populates="events")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[PaymentAttemptPhase] = mapped_column(
        SAEnum(PaymentAttemptPhase, name="payment_attempt_phase_enum", native_enum=False),
        nullable=False,
    )
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
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

    payment: Mapped[Payment] = relationship("Payment", back_populates="attempts")

    __table_args__ = (
        UniqueConstraint(
            "payment_id",
            "phase",
            "attempt_no",
            name="uq_payment_attempts_phase_order",
        ),
        Index("ix_payment_attempts_payment_phase", "payment_id", "phase"),
        Index("ix_payment_attempts_phase_updated", "phase", "updated_at"),
    )


__all__ = [
    "Payment",
    "PaymentAttempt",
    "PaymentEvent",
    "PaymentStatus",
    "Provider",
]
