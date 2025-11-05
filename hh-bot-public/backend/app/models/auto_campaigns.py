from __future__ import annotations

import enum
from datetime import datetime, time
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Time,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, _utcnow

JsonType = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CampaignMode(str, enum.Enum):
    STRICT = "strict"
    WIDE = "wide"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.DRAFT,
        nullable=False,
    )
    mode: Mapped[CampaignMode] = mapped_column(
        Enum(CampaignMode, name="campaign_mode"),
        nullable=False,
    )
    daily_quota_target: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    default_window_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("campaign_delivery_windows.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )
    cooldown_policy_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("campaign_cooldown_policies.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    windows: Mapped[list["CampaignDeliveryWindow"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="CampaignDeliveryWindow.campaign_id",
        primaryjoin="Campaign.id == CampaignDeliveryWindow.campaign_id",
    )
    steps: Mapped[list["CampaignStep"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    frequency_caps: Mapped[Optional["CampaignFrequencyCaps"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
        foreign_keys="CampaignFrequencyCaps.campaign_id",
        primaryjoin="Campaign.id == CampaignFrequencyCaps.campaign_id",
    )
    cooldown_policy: Mapped[Optional["CampaignCooldownPolicy"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
        foreign_keys="CampaignCooldownPolicy.campaign_id",
        primaryjoin="Campaign.id == CampaignCooldownPolicy.campaign_id",
    )
    runs: Mapped[list["CampaignRun"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    delivery_logs: Mapped[list["CampaignDeliveryLog"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notifications: Mapped[list["CampaignNotification"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CampaignDeliveryWindow(Base, TimestampMixin):
    __tablename__ = "campaign_delivery_windows"
    __table_args__ = (
        CheckConstraint("start_utc < end_utc", name="delivery_windows_time_range_chk"),
        CheckConstraint("length(days_mask) = 7", name="delivery_windows_days_mask_len_chk"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    start_utc: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    end_utc: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    days_mask: Mapped[str] = mapped_column(String(7), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    campaign: Mapped[Campaign] = relationship(
        back_populates="windows",
        foreign_keys=[campaign_id],
        primaryjoin="CampaignDeliveryWindow.campaign_id == Campaign.id",
    )
    steps: Mapped[list["CampaignStep"]] = relationship(
        back_populates="window",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SkipPolicy(str, enum.Enum):
    MANUAL = "manual"
    AUTO = "auto"


class CampaignStep(Base, TimestampMixin):
    __tablename__ = "campaign_steps"
    __table_args__ = (
        UniqueConstraint("campaign_id", "step_order", name="uniq_steps_per_campaign"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    vacancy_filter: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False)
    message_template_id: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_window_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_delivery_windows.id", ondelete="RESTRICT", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    skip_policy: Mapped[SkipPolicy] = mapped_column(
        Enum(SkipPolicy, name="campaign_skip_policy"),
        default=SkipPolicy.MANUAL,
        nullable=False,
    )

    campaign: Mapped[Campaign] = relationship(back_populates="steps")
    window: Mapped[CampaignDeliveryWindow] = relationship(back_populates="steps")
    delivery_logs: Mapped[list["CampaignDeliveryLog"]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CampaignFrequencyCaps(Base, TimestampMixin):
    __tablename__ = "campaign_frequency_caps"
    __table_args__ = (UniqueConstraint("campaign_id", name="uniq_caps_per_campaign"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    per_company: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    campaign: Mapped[Campaign] = relationship(
        back_populates="frequency_caps",
        foreign_keys=[campaign_id],
    )


class CooldownStrategy(str, enum.Enum):
    EXP = "exp"
    LINEAR = "linear"


class CampaignCooldownPolicy(Base, TimestampMixin):
    __tablename__ = "campaign_cooldown_policies"
    __table_args__ = (UniqueConstraint("campaign_id", name="uniq_cooldown_per_campaign"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    base_delay_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=60_000)
    max_delay_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=900_000)
    strategy: Mapped[CooldownStrategy] = mapped_column(
        Enum(CooldownStrategy, name="campaign_cooldown_strategy"),
        nullable=False,
        default=CooldownStrategy.EXP,
    )
    error_streak_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    campaign: Mapped[Campaign] = relationship(
        back_populates="cooldown_policy",
        foreign_keys=[campaign_id],
    )


class CampaignRun(Base):
    __tablename__ = "campaign_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    run_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    run_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_by: Mapped[str] = mapped_column(String(16), nullable=False, default="system")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delay_applied_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    campaign: Mapped[Campaign] = relationship(back_populates="runs")
    delivery_logs: Mapped[list["CampaignDeliveryLog"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DeliveryLogStatus(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class CampaignDeliveryLog(Base):
    __tablename__ = "campaign_delivery_logs"
    __table_args__ = (
        UniqueConstraint("campaign_id", "vacancy_id", "step_id", name="uniq_delivery_guard"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    campaign_run_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("campaign_runs.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )
    step_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("campaign_steps.id", ondelete="SET NULL", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )
    vacancy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[DeliveryLogStatus] = mapped_column(
        Enum(DeliveryLogStatus, name="campaign_delivery_status"),
        nullable=False,
    )
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )

    campaign: Mapped[Campaign] = relationship(back_populates="delivery_logs")
    run: Mapped[Optional[CampaignRun]] = relationship(back_populates="delivery_logs")
    step: Mapped[Optional[CampaignStep]] = relationship(back_populates="delivery_logs")


class CampaignCompanyBlacklist(Base):
    __tablename__ = "campaign_company_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id_external: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CampaignUserOptOut(Base):
    __tablename__ = "campaign_user_opt_out"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )


class CampaignNotificationType(str, enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
    EMPTY = "empty"
    PAUSED = "paused"
    LIMIT_REACHED = "limit_reached"
    RESUMED = "resumed"


class CampaignNotificationChannel(str, enum.Enum):
    BOT = "bot"
    EMAIL = "email"


class CampaignNotification(Base):
    __tablename__ = "campaign_notifications"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "type",
            "sent_at",
            "channel",
            name="uniq_notifications_dedup",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    type: Mapped[CampaignNotificationType] = mapped_column(
        Enum(CampaignNotificationType, name="campaign_notification_type"),
        nullable=False,
    )
    channel: Mapped[CampaignNotificationChannel] = mapped_column(
        Enum(CampaignNotificationChannel, name="campaign_notification_channel"),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="notifications")


class CampaignAuditLog(Base):
    __tablename__ = "campaign_audit_log"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "action",
            "idempotency_key",
            name="uniq_audit_idempotency",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )
    actor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )
