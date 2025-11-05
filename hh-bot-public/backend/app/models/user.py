# app/models/user.py
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from backend.app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_activity = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    search_queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    trials = relationship("UserTrial", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    quotas = relationship("ApplicationQuota", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    blacklisted_companies = relationship(
        "CompanyBlacklistEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
