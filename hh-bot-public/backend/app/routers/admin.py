# backend/app/routers/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.models.plan import Plan
from backend.app.schemas.plan import PlanOut
from backend.app.security_admin import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/ping")
def admin_ping() -> dict[str, bool]:
    return {"ok": True}


@router.get("/plans", response_model=list[PlanOut])
async def admin_plans(db: AsyncSession = Depends(get_db)) -> list[PlanOut]:
    result = await db.execute(select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order.asc()))
    plans = result.scalars().all()
    return [PlanOut.model_validate(plan) for plan in plans]
