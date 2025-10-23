from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from backend.app.models import User
from backend.app.models.billing import Plan, PlanPeriod, Subscription, SubscriptionStatus

FREE_TRIAL_PLAN = {
    "code": "FREE_TRIAL",
    "period": PlanPeriod.TRIAL,
    "is_recurring": False,
    "amount_minor": 0,
    "currency": "RUB",
    "granted_quota": 10,
    "non_renewable": True,
    "display_name": "Free Trial",
}

PAID_PLANS = [
    {
        "code": "WEEKLY",
        "period": PlanPeriod.WEEK,
        "is_recurring": True,
        "amount_minor": 69000,
        "currency": "RUB",
        "granted_quota": 0,
        "non_renewable": False,
        "display_name": "Weekly",
    },
    {
        "code": "MONTHLY",
        "period": PlanPeriod.MONTH,
        "is_recurring": True,
        "amount_minor": 190000,
        "currency": "RUB",
        "granted_quota": 0,
        "non_renewable": False,
        "display_name": "Monthly",
    },
]


async def seed_plans(session) -> None:
    existing = await session.get(Plan, "FREE_TRIAL")
    if existing:
        return

    plans = [Plan(**FREE_TRIAL_PLAN)]
    for cfg in PAID_PLANS:
        plans.append(Plan(**cfg))

    session.add_all(plans)
    await session.commit()


async def create_user(session, token: str | None = None) -> dict[str, int | str]:
    user = User(tg_id=token or f"u-{uuid.uuid4().hex[:8]}")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": user.id, "token": user.tg_id}


@pytest.mark.asyncio
async def test_trial_activate_once_ok(client, session_factory):
    async with session_factory() as session:
        await seed_plans(session)
        user = await create_user(session, "trial-user")

    headers = {"X-User-Id": user["token"]}

    resp = await client.post("/api/v1/trial/activate", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["plan_code"] == "FREE_TRIAL"
    assert data["granted"] == 10
    assert data["consumed"] == 0

    resp2 = await client.post("/api/v1/trial/activate", headers=headers)
    assert resp2.status_code == 409
    assert resp2.json()["code"] == "TRIAL_ALREADY_USED"


@pytest.mark.asyncio
async def test_apply_decrements_quota_and_returns_remaining(client, session_factory):
    async with session_factory() as session:
        await seed_plans(session)
        user = await create_user(session, "quota-user")

    headers = {"X-User-Id": user["token"]}
    await client.post("/api/v1/trial/activate", headers=headers)

    for idx in range(10):
        resp = await client.post(
            "/api/v1/apply",
            headers=headers,
            json={"vacancy_id": f"vac-{idx}"},
        )
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["applied"] is True
        assert payload.get("remaining") == 9 - idx


@pytest.mark.asyncio
async def test_apply_exhausted_returns_403(client, session_factory):
    async with session_factory() as session:
        await seed_plans(session)
        user = await create_user(session, "exhaust-user")

    headers = {"X-User-Id": user["token"]}
    await client.post("/api/v1/trial/activate", headers=headers)

    for idx in range(10):
        resp = await client.post(
            "/api/v1/apply",
            headers=headers,
            json={"vacancy_id": f"busy-{idx}"},
        )
        assert resp.status_code == 200, resp.text

    resp = await client.post(
        "/api/v1/apply",
        headers=headers,
        json={"vacancy_id": "busy-over"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "TRIAL_EXHAUSTED"


@pytest.mark.asyncio
async def test_apply_idempotent_same_vacancy(client, session_factory):
    async with session_factory() as session:
        await seed_plans(session)
        user = await create_user(session, "idem-user")

    headers = {"X-User-Id": user["token"]}
    await client.post("/api/v1/trial/activate", headers=headers)

    first = await client.post(
        "/api/v1/apply",
        headers=headers,
        json={"vacancy_id": "dup-1"},
    )
    assert first.status_code == 200
    remaining_after_first = first.json()["remaining"]

    dup = await client.post(
        "/api/v1/apply",
        headers=headers,
        json={"vacancy_id": "dup-1"},
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "DUPLICATE_APPLY"

    quota = await client.get("/api/v1/quota", headers=headers)
    assert quota.status_code == 200
    assert quota.json()["remaining"] == remaining_after_first


@pytest.mark.asyncio
async def test_apply_requires_subscription_when_no_trial(client, session_factory):
    async with session_factory() as session:
        await seed_plans(session)
        user = await create_user(session, "no-trial-user")

    headers = {"X-User-Id": user["token"]}
    resp = await client.post(
        "/api/v1/apply",
        headers=headers,
        json={"vacancy_id": "need-sub"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "SUBSCRIPTION_REQUIRED"


@pytest.mark.asyncio
async def test_apply_with_active_subscription_no_quota(client, session_factory):
    async with session_factory() as session:
        await seed_plans(session)
        user = await create_user(session, "paid-user")
        subscription = Subscription(
            user_id=user["id"],
            plan_code="WEEKLY",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc) - timedelta(hours=1),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=7),
            next_charge_at=None,
            cancel_at=None,
            cancel_at_period_end=False,
        )
        session.add(subscription)
        await session.commit()

    headers = {"X-User-Id": user["token"]}
    resp = await client.post(
        "/api/v1/apply",
        headers=headers,
        json={"vacancy_id": "paid-1"},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["applied"] is True
    assert "remaining" not in payload

    second = await client.post(
        "/api/v1/apply",
        headers=headers,
        json={"vacancy_id": "paid-2"},
    )
    assert second.status_code == 200
    assert "remaining" not in second.json()
