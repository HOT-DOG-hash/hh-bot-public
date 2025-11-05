from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class UserSetting(Base, TimestampMixin):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    strict_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    workday_start_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=6)
    workday_end_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=24)
    preferred_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    user: Mapped["User"] = relationship(back_populates="settings")


if TYPE_CHECKING:
    from backend.app.models.user import User
