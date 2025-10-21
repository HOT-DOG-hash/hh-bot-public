from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.models import Resume
from backend.app.schemas.resume import ResumeOut

router = APIRouter()


@router.get("/resumes", response_model=list[ResumeOut])
async def list_resumes(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Resume).limit(50))
    return res.scalars().all()
