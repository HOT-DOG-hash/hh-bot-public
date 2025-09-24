from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from ...core.db import get_db
from ...models import SearchQuery, User
from ...security import admin_guard

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db), _: bool = Depends(admin_guard)):
    total_users = await db.scalar(select(func.count()).select_from(User))

    active_today_stmt = (
        select(func.count())
        .select_from(User)
        .where(func.date(User.last_activity) == func.date(func.now()))
    )
    active_today = await db.scalar(active_today_stmt)

    searches_24h_stmt = (
        select(func.count())
        .select_from(SearchQuery)
        .where(SearchQuery.created_at >= func.now() - func.make_interval(hours=24))
    )
    searches_24h = await db.scalar(searches_24h_stmt)

    return {
        "total_users": total_users or 0,
        "active_today": active_today or 0,
        "searches_24h": searches_24h or 0,
    }
