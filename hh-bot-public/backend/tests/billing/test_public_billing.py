import pytest


@pytest.mark.asyncio
async def test_get_public_plans(client):
    resp = await client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plans"][0]["code"] == "FREE_TRIAL"
    assert data["plans"][1]["code"] == "WEEKLY"
    assert data["plans"][2]["granted_quota"] == 800


@pytest.mark.asyncio
async def test_trial_activation_and_subscription_flow(client):
    payload = {
        "telegram_id": "tg-user-001",
    }
    resp = await client.post("/api/v1/billing/trial/activate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscription"]["plan_code"] == "FREE_TRIAL"
    assert body["subscription"]["status"] == "trial"
    assert body["quota"]["trial_limit"] == 10

    quota_resp = await client.get("/api/v1/quota", params={"telegram_id": "tg-user-001"})
    assert quota_resp.status_code == 200
    quota_data = quota_resp.json()
    assert quota_data["remaining_trial"] == 10

    extend_payload = {
        "telegram_id": "tg-user-001",
        "plan_code": "WEEKLY",
    }
    extend_resp = await client.post("/api/v1/billing/subscription/extend", json=extend_payload)
    assert extend_resp.status_code == 200
    extend_data = extend_resp.json()
    assert extend_data["subscription"]["plan_code"] == "WEEKLY"
    assert extend_data["subscription"]["status"] == "active"
