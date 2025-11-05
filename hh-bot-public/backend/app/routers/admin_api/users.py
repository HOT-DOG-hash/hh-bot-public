from fastapi import APIRouter
router = APIRouter()

@router.get("/users")
async def admin_list_users():
    return {"items": [], "total": 0}
