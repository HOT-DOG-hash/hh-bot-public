import base64

import pytest


@pytest.mark.asyncio
async def test_admin_plans_returns_seeded_plans(client):
    credentials = base64.b64encode(b"admin:secret").decode()
    response = await client.get(
        "/admin/plans",
        headers={"Authorization": f"Basic {credentials}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert [plan["code"] for plan in data] == ["FREE_TRIAL", "WEEKLY", "MONTHLY"]
    assert data[0]["granted_quota"] == 10
    assert data[1]["amount_minor"] == 99_000
    assert data[2]["duration_days"] == 30
