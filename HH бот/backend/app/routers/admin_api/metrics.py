from fastapi import APIRouter
router = APIRouter()

@router.get("/stats")
async def admin_stats_stub():
    return {
        "users": {"total": 0, "active": 0},
        "payments": {"today": 0, "month": 0},
        "responses": {"today": 0, "month": 0},
    }
