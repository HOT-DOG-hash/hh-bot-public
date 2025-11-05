from fastapi import APIRouter
from .metrics import router as metrics_router
from .users import router as users_router
from .broadcasts import router as broadcasts_router

router = APIRouter()
router.include_router(metrics_router)
router.include_router(users_router)
router.include_router(broadcasts_router)
