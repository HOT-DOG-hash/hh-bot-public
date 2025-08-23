from fastapi import APIRouter
router = APIRouter()

@router.get("/broadcasts")
async def admin_broadcasts_stub():
    return {"items": []}
