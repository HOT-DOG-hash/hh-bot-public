import asyncio
import logging
import os
import signal
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import text

from backend.app.core.db import get_engine
from backend.app.main import app, start_bot, stop_bot

try:  # pragma: no cover - optional optimisation
    import uvloop  # type: ignore

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:  # pragma: no cover - env-specific
    pass


async def _check_dependencies() -> None:
    engine = get_engine()
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        client: Optional[Redis] = None
        try:
            client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await client.ping()
        finally:
            if client is not None:
                await client.aclose()


async def _wait_for_dependencies(max_attempts: int = 8) -> None:
    delay = 2
    attempt = 0
    while True:
        try:
            await _check_dependencies()
            logging.info("Bot dependencies are ready.")
            return
        except Exception as exc:
            attempt += 1
            logging.warning("Dependencies not ready (attempt %s/%s): %s", attempt, max_attempts, exc)
            if attempt >= max_attempts:
                logging.error("Giving up waiting for dependencies.")
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


async def _runner():
    await _wait_for_dependencies()
    await start_bot(app)
    loop = asyncio.get_running_loop()
    stop_future = loop.create_future()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_future.set_result, None)
        except NotImplementedError:  # pragma: no cover - Windows/WSL limitation
            pass
    await stop_future
    await stop_bot(app)


if __name__ == "__main__":
    asyncio.run(_runner())
