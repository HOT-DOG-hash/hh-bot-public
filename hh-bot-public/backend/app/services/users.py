from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> Optional[User]:
    stmt = select(User).where(User.tg_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def ensure_user(
    session: AsyncSession,
    *,
    telegram_id: str,
) -> User:
    """
    Creates a new user if it does not exist yet and returns the instance.
    Only the telegram identifier is mandatory for MVP onboarding.
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is not None:
        return user

    user = User(tg_id=telegram_id, is_active=True)
    session.add(user)
    await session.flush()
    return user
