# app/models/search_query.py
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from backend.app.models.base import Base


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=True, index=True)
    query = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="search_queries")
