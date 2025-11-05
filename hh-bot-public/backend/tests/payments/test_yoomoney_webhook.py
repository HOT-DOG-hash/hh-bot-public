from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.app.core.db import get_session_factory
from backend.app.models.payments import Payment, PaymentStatus
from backend.app.models.subscription import Subscription, SubscriptionStatus
from backend.tests.payments.helpers import create_user


async def _get_payment(payment_id: int) -> Payment:
    session_factory = get_session_factory()
    async with session_factory() as session:
        payment = await session.get(Payment, payment_id)
        if payment is None:
            raise AssertionError("payment not found")
        await session.refresh(payment)
        return payment


@pytest.mark.asyncio
async def test_webhook_success_flow_updates_subscription(client):
    user_id = await create_user()
    init_payload = {
        "user_id": user_id,
        "plan_code": "WEEKLY",
        "idempotency_key": "webhook-flow-1",
    }
    init_resp = await client.post("/api/v1/payments/initiate", json=init_payload)
    assert init_resp.status_code == 200
    payment_id = init_resp.json()["payment_id"]

    pending_payload = {
        "event_id": "evt-weekly-pending",
        "status": PaymentStatus.PENDING.value,
        "payment_id": payment_id,
    }
    pending_resp = await client.post("/api/v1/payments/webhook", json=pending_payload)
    assert pending_resp.status_code == 200
    pending_data = pending_resp.json()
    assert pending_data["status"] == PaymentStatus.PENDING.value
    assert pending_data["processed"] is True

    occurred_at = datetime.now(timezone.utc).isoformat()
    success_payload = {
        "event_id": "evt-weekly-success",
        "status": PaymentStatus.SUCCEEDED.value,
        "payment_id": payment_id,
        "provider_payment_id": "provider-123",
        "occurred_at": occurred_at,
        "raw": {"provider": "yoomoney"},
    }
    success_resp = await client.post("/api/v1/payments/webhook", json=success_payload)
    assert success_resp.status_code == 200
    success_data = success_resp.json()
    assert success_data["status"] == PaymentStatus.SUCCEEDED.value
    assert success_data["processed"] is True
    assert success_data["deduplicated"] is False

    duplicate_resp = await client.post("/api/v1/payments/webhook", json=success_payload)
    assert duplicate_resp.status_code == 200
    duplicate_data = duplicate_resp.json()
    assert duplicate_data["deduplicated"] is True
    assert duplicate_data["processed"] is False

    payment = await _get_payment(payment_id)
    assert payment.status is PaymentStatus.SUCCEEDED
    assert payment.provider_payment_id == "provider-123"

    session_factory = get_session_factory()
    async with session_factory() as session:
        sub_result = await session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = sub_result.scalar_one_or_none()
        assert subscription is not None
        assert subscription.plan_code == "WEEKLY"
        assert subscription.status is SubscriptionStatus.ACTIVE

    metrics_resp = await client.get("/metrics")
    assert metrics_resp.status_code == 200
    lines = metrics_resp.text.splitlines()
    success_line = next(
        (line for line in lines if line.startswith('payments_succeeded_total{plan_code="WEEKLY"}')),
        None,
    )
    assert success_line is not None


@pytest.mark.asyncio
async def test_webhook_invalid_payload_is_ignored(client):
    payload = {
        "event_id": "evt-missing",
        "status": PaymentStatus.FAILED.value,
        "payment_id": 999999,
    }
    resp = await client.post("/api/v1/payments/webhook", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] is False
    assert data["payment_id"] is None
