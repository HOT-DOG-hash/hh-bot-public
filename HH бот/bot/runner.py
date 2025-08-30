import asyncio
import signal
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # не критично, но ускоряет
except Exception:
    pass

from backend.app.main import start_bot, stop_bot, app

async def _runner():
    await start_bot(app)
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set_result, None)
        except NotImplementedError:
            # на всякий случай для окружений без signal handlers
            pass
    await stop
    await stop_bot(app)

if __name__ == "__main__":
    asyncio.run(_runner())
