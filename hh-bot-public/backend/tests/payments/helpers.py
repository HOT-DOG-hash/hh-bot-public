from __future__ import annotations

import uuid
from typing import cast

from backend.app.core.db import get_session_factory
from backend.app.models.user import User


async def create_user() -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(tg_id=f"test-{uuid.uuid4()}", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return cast(int, user.id)
