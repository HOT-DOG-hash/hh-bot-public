from fastapi import APIRouter
router = APIRouter()

@router.get("/stats")
async def stats_stub():
    return {"users_total": 0, "resumes_total": 0, "responses_today": 0}
