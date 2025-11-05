from fastapi import APIRouter
from .resume import router as resumes_router
from .search import router as search_router
from .stats import router as stats_router

router = APIRouter()
router.include_router(resumes_router)
router.include_router(search_router)
router.include_router(stats_router)
