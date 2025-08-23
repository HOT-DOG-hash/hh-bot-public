# seed_dev.py
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.user import User
from app.models.resume import Resume


async def main():
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        # 1) Находим/создаём пользователя
        tg_id = "tg_123"
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(tg_id=tg_id, is_active=True)
            session.add(user)
            await session.flush()  # получаем user.id без commit

        # 2) Находим/создаём резюме
        hh_id = "HH-XYZ"
        result = await session.execute(
            select(Resume).where(Resume.user_id == user.id, Resume.hh_id == hh_id)
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            resume = Resume(user_id=user.id, hh_id=hh_id, title="Python Dev")
            session.add(resume)

        await session.commit()
        print("Seed done")


if __name__ == "__main__":
    asyncio.run(main())
