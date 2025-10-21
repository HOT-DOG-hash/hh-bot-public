from __future__ import annotations

import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest
from backend.app.core import metrics
from backend.app.core.config import settings
from backend.app.models import Payment, PaymentAttempt, PaymentEvent, Subscription, User
from backend.app.payments.base import PaymentInvoice, PaymentProviderError
from backend.app.payments.yoomoney import provider as yoomoney_provider
from sqlalchemy import func, select

API_PREFIX = "/api/v1/payments"


@pytest.fixture(autouse=True)
def _reset_metrics():
    for metric in (
        metrics.payments_initiated_total,
        metrics.payment_webhooks_total,
        metrics.payments_status_total,
        metrics.yoomoney_api_latency_ms,
        metrics.webhook_processing_ms,
    ):
        metric._values.clear()  # type: ignore[attr-defined]


async def _create_user(session) -> User:
    user = User(tg_id=f"user-{uuid4().hex[:8]}")
    session.add(user)
    await session.flush()
    return user


def _signature(payload: dict[str, Any], secret: str) -> str:
    body = json.dumps(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), body, "sha256").hexdigest()


@pytest.mark.asyncio
async def test_init_idempotent(client, session_factory, monkeypatch):
    calls: list[str | None] = []

    async def fake_create_payment(**kwargs):
        calls.append(kwargs.get("idempotence_key"))
        return PaymentInvoice(
            external_id="pay-123",
            confirmation_url="https://pay.example/123",
            status="pending",
            created_at=datetime.now(timezone.utc),
            raw={"id": "pay-123", "status": "pending"},
        )

    monkeypatch.setattr(yoomoney_provider, "create_payment", fake_create_payment)

    headers = {"X-User-Id": "user-idempotent"}
    payload = {"plan_code": "WEEKLY", "idempotency_key": "idem-1"}

    resp1 = await client.post(f"{API_PREFIX}/initiate", json=payload, headers=headers)
    assert resp1.status_code == 200
    resp2 = await client.post(f"{API_PREFIX}/initiate", json=payload, headers=headers)
    assert resp2.status_code == 200
    assert len(calls) == 1
    assert resp1.json()["payment_id"] == resp2.json()["payment_id"]

    async with session_factory() as session:
        count = await session.scalar(select(func.count(Payment.id)))
        assert count == 1


@pytest.mark.asyncio
async def test_webhook_dedup(client, session_factory, monkeypatch):
    secret = "test-secret"
    monkeypatch.setattr(settings, "yoomoney_webhook_secret", secret)

    async with session_factory() as session:
        user = await _create_user(session)
        payment = Payment(
            user_id=user.id,
            provider="yoomoney",
            external_id="pay-1",
            plan="WEEKLY",
            amount=69000,
            currency="RUB",
            status="pending",
            payload_json={},
            idempotency_key="idem-webhook",
            confirmation_url="https://pay/1",
        )
        session.add(payment)
        await session.commit()
        payment_id = payment.id

    payload = {
        "event_id": "evt-1",
        "event": "payment.succeeded",
        "object": {
            "id": "pay-1",
            "status": "succeeded",
            "metadata": {"idempotency_key": "idem-webhook"},
        },
    }
    headers = {
        "Content-Type": "application/json",
        "X-YooMoney-Signature": _signature(payload, secret),
    }

    first = await client.post(f"{API_PREFIX}/webhook", data=json.dumps(payload), headers=headers)
    assert first.status_code == 200

    second = await client.post(f"{API_PREFIX}/webhook", data=json.dumps(payload), headers=headers)
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"

    async with session_factory() as session:
        payment = await session.get(Payment, payment_id)
        assert payment.status == "succeeded"
        events = await session.execute(
            select(PaymentEvent).where(PaymentEvent.payment_id == payment_id)
        )
        assert len(events.scalars().all()) == 1


@pytest.mark.asyncio
async def test_fsm_transitions(client, session_factory, monkeypatch):
    secret = "fsm-secret"
    monkeypatch.setattr(settings, "yoomoney_webhook_secret", secret)

    async with session_factory() as session:
        user = await _create_user(session)
        payment = Payment(
            user_id=user.id,
            provider="yoomoney",
            external_id="pay-fsm",
            plan="WEEKLY",
            amount=69000,
            currency="RUB",
            status="pending",
            payload_json={},
            idempotency_key="idem-fsm",
            confirmation_url="https://pay/fsm",
        )
        session.add(payment)
        await session.commit()
        payment_id = payment.id
        user_id = user.id

    payload = {
        "event_id": "evt-success",
        "event": "payment.succeeded",
        "object": {
            "id": "pay-fsm",
            "status": "succeeded",
            "metadata": {"idempotency_key": "idem-fsm"},
        },
    }
    headers = {
        "Content-Type": "application/json",
        "X-YooMoney-Signature": _signature(payload, secret),
    }
    await client.post(f"{API_PREFIX}/webhook", data=json.dumps(payload), headers=headers)

    payload["event_id"] = "evt-success-2"
    await client.post(f"{API_PREFIX}/webhook", data=json.dumps(payload), headers=headers)

    async with session_factory() as session:
        other = Payment(
            user_id=user_id,
            provider="yoomoney",
            external_id="pay-exp",
            plan="WEEKLY",
            amount=69000,
            currency="RUB",
            status="pending",
            payload_json={},
            idempotency_key="idem-exp",
            confirmation_url="https://pay/exp",
        )
        session.add(other)
        await session.commit()

    expired_payload = {
        "event_id": "evt-expired",
        "event": "payment.canceled",
        "object": {
            "id": "pay-exp",
            "status": "expired",
            "metadata": {"idempotency_key": "idem-exp"},
        },
    }
    headers_exp = {
        "Content-Type": "application/json",
        "X-YooMoney-Signature": _signature(expired_payload, secret),
    }
    await client.post(
        f"{API_PREFIX}/webhook", data=json.dumps(expired_payload), headers=headers_exp
    )

    async with session_factory() as session:
        payment = await session.get(Payment, payment_id)
        assert payment.status == "succeeded"
        subscription = await session.scalar(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        assert subscription is not None
        expired_payment = await session.scalar(
            select(Payment).where(Payment.idempotency_key == "idem-exp")
        )
        assert expired_payment.status == "expired"


@pytest.mark.asyncio
async def test_order_tolerance(client, session_factory, monkeypatch):
    secret = "order-secret"
    monkeypatch.setattr(settings, "yoomoney_webhook_secret", secret)

    async with session_factory() as session:
        user = await _create_user(session)
        payment = Payment(
            user_id=user.id,
            provider="yoomoney",
            external_id="pay-order",
            plan="WEEKLY",
            amount=69000,
            currency="RUB",
            status="pending",
            payload_json={},
            idempotency_key="idem-order",
            confirmation_url="https://pay/order",
        )
        session.add(payment)
        await session.commit()
        payment_id = payment.id

    succeeded = {
        "event_id": "evt-order-s",
        "event": "payment.succeeded",
        "object": {
            "id": "pay-order",
            "status": "succeeded",
            "metadata": {"idempotency_key": "idem-order"},
        },
    }
    pending = {
        "event_id": "evt-order-p",
        "event": "payment.pending",
        "object": {
            "id": "pay-order",
            "status": "pending",
            "metadata": {"idempotency_key": "idem-order"},
        },
    }
    headers1 = {
        "Content-Type": "application/json",
        "X-YooMoney-Signature": _signature(succeeded, secret),
    }
    headers2 = {
        "Content-Type": "application/json",
        "X-YooMoney-Signature": _signature(pending, secret),
    }

    await client.post(f"{API_PREFIX}/webhook", data=json.dumps(succeeded), headers=headers1)
    await client.post(f"{API_PREFIX}/webhook", data=json.dumps(pending), headers=headers2)

    async with session_factory() as session:
        payment = await session.get(Payment, payment_id)
        assert payment.status == "succeeded"


@pytest.mark.asyncio
async def test_timeouts_and_failures_do_not_duplicate_payments(
    client, session_factory, monkeypatch
):
    async def failing_create(**kwargs):
        raise PaymentProviderError("timeout")

    monkeypatch.setattr(yoomoney_provider, "create_payment", failing_create)

    headers = {"X-User-Id": "user-timeout"}
    payload = {"plan_code": "WEEKLY", "idempotency_key": "idem-timeout"}
    resp = await client.post(f"{API_PREFIX}/initiate", json=payload, headers=headers)
    assert resp.status_code == 502

    async with session_factory() as session:
        payments = await session.execute(select(Payment))
        rows = payments.scalars().all()
        assert len(rows) == 1
        assert rows[0].status == "failed"
        attempts = await session.execute(
            select(PaymentAttempt).where(PaymentAttempt.payment_id == rows[0].id)
        )
        assert attempts.scalar_one().phase == "init"


@pytest.mark.asyncio
async def test_metrics_smoke(client, session_factory, monkeypatch):
    secret = "metric-secret"
    monkeypatch.setattr(settings, "yoomoney_webhook_secret", secret)

    async def fake_create(**kwargs):
        return PaymentInvoice(
            external_id="pay-metrics",
            confirmation_url="https://pay/metrics",
            status="pending",
            created_at=datetime.now(timezone.utc),
            raw={},
        )

    monkeypatch.setattr(yoomoney_provider, "create_payment", fake_create)

    headers = {"X-User-Id": "user-metrics"}
    payload = {"plan_code": "WEEKLY", "idempotency_key": "idem-metrics"}

    await client.post(f"{API_PREFIX}/initiate", json=payload, headers=headers)

    webhook_payload = {
        "event_id": "evt-metrics",
        "event": "payment.succeeded",
        "object": {
            "id": "pay-metrics",
            "status": "succeeded",
            "metadata": {"idempotency_key": "idem-metrics"},
        },
    }
    headers_webhook = {
        "Content-Type": "application/json",
        "X-YooMoney-Signature": _signature(webhook_payload, secret),
    }
    await client.post(
        f"{API_PREFIX}/webhook", data=json.dumps(webhook_payload), headers=headers_webhook
    )

    assert metrics.payments_initiated_total.value(plan_code="WEEKLY") == 1
    assert metrics.payment_webhooks_total.value(event_type="payment.succeeded") == 1
    assert metrics.payments_status_total.value(status="succeeded") == 1
