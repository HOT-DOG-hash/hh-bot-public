from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.redis import init_redis, close_redis
# ВАЖНО: убираем импорт engine/Base и create_all – миграциями управляет Alembic

# Роутеры
from app.routers import bot_api, admin_api
from app.routers.health import router as meta_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting application", app=settings.app_name)
    await init_redis()
    try:
        yield
    finally:
        await close_redis()
        logger.info("🛑 Shutting down application")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    # CORS — при необходимости добавь домены фронта
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роутеры
    app.include_router(bot_api.router, prefix="/api/bot", tags=["bot"])
    app.include_router(admin_api.router, prefix="/api/admin", tags=["admin"])
    app.include_router(meta_router)
    app.include_router(bot_api.router, prefix="/bot_api")
    app.include_router(admin_api.router, prefix="/admin_api")
    
    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    return app


app = create_app()
