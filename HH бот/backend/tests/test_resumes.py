import pytest

@pytest.mark.asyncio
async def test_resumes_empty(client):
    r = await client.get("/api/bot/resumes")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
