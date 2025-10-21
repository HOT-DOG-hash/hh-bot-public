import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.text.strip() == "ok"
