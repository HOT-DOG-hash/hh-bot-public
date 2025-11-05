import pytest


@pytest.mark.asyncio
async def test_quota_consume_and_limits(client):
    # activate trial via billing endpoint
    activate_resp = await client.post(
        "/api/v1/billing/trial/activate",
        json={"telegram_id": "tg-quota-1"},
    )
    assert activate_resp.status_code == 200

    consume_payload = {
        "telegram_id": "tg-quota-1",
        "count": 4,
    }
    consume_resp = await client.post("/api/v1/quota/consume", json=consume_payload)
    assert consume_resp.status_code == 200
    data = consume_resp.json()
    assert data["trial_used"] == 4
    assert data["remaining_trial"] == 6

    # cannot consume beyond remaining trial
    too_much = {
        "telegram_id": "tg-quota-1",
        "count": 20,
    }
    too_much_resp = await client.post("/api/v1/quota/consume", json=too_much)
    assert too_much_resp.status_code == 400
    assert "quota" in too_much_resp.json()["detail"]
