# backend/app/routers/admin.py
from fastapi import APIRouter, Depends

from backend.app.security_admin import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/ping")
def admin_ping():
    return {"ok": True}
