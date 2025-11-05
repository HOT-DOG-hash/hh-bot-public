from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from backend.app.models.base import Base


class CompanyBlacklistEntry(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "companies_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp())

    user: Mapped["User"] = relationship(back_populates="blacklisted_companies")


from backend.app.models.user import User  # noqa: E402
