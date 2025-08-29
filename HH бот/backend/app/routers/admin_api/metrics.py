from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from ...database import get_db
from ...models import User
from ...security import admin_guard

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db), _: bool = Depends(admin_guard)):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_today = (await db.execute(text(
        "SELECT COUNT(*) FROM users WHERE (last_activity AT TIME ZONE 'UTC')::date = (now() AT TIME ZONE 'UTC')::date"
    ))).scalar_one()
    searches_24h = (await db.execute(text(
        "SELECT COUNT(*) FROM search_queries WHERE created_at >= now() - interval '24 hours'"
    ))).scalar_one()
    return {"total_users": total_users, "active_today": active_today, "searches_24h": searches_24h}
