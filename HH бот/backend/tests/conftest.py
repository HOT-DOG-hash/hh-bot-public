import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

# Правильная асинхронная фикстура клиента под httpx 0.28+
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
