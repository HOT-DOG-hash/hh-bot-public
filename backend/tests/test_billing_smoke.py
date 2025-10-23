from __future__ import annotations

from datetime import datetime, timezone

import pytest
from backend.app.core.config import settings
from backend.app.models import Payment, Subscription
from backend.app.models.billing import SubscriptionStatus
from backend.app.models.payments import PaymentStatus
from backend.app.payments.base import PaymentInvoice, PaymentStatus as ProviderPaymentStatus
from backend.app.payments.yoomoney import provider as yoomoney_provider
from sqlalchemy import select


@pytest.mark.asyncio
async def test_billing_flow(session_factory, client, monkeypatch):
    created_ids: list[str] = []

    async def fake_create_payment(**kwargs):
        created_ids.append("pay-ext-1")
        return PaymentInvoice(
            external_id="pay-ext-1",
            confirmation_url="https://pay.example/1",
            status="created",
            created_at=datetime.now(timezone.utc),
            raw={
                "confirmation": {"confirmation_url": "https://pay.example/1"},
                "status": "created",
            },
        )

    async def fake_get_payment_status(external_id: str):
        assert external_id == "pay-ext-1"
        return ProviderPaymentStatus(
            external_id=external_id,
            status="succeeded",
            paid_at=datetime.now(timezone.utc),
            raw={"status": "succeeded"},
        )

    monkeypatch.setattr(yoomoney_provider, "create_payment", fake_create_payment)
    monkeypatch.setattr(yoomoney_provider, "get_payment_status", fake_get_payment_status)

    premium_original = settings.premium_enabled
    provider_original = settings.payment_provider
    settings.premium_enabled = True
    settings.payment_provider = "yoomoney"

    try:
        response = await client.post(
            "/billing/create",
            params={"plan": "MONTHLY"},
            headers={"X-User-Id": "123"},
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["external_id"] == "pay-ext-1"
        assert payload["pay_url"] == "https://pay.example/1"
        assert payload["status"] == PaymentStatus.PENDING.value

        response_repeat = await client.post(
            "/billing/create",
            params={"plan": "MONTHLY"},
            headers={"X-User-Id": "123"},
        )
        assert response_repeat.status_code == 201
        assert response_repeat.json()["external_id"] == "pay-ext-1"
        assert len(created_ids) == 1

        status_response = await client.get(
            "/billing/status/pay-ext-1", headers={"X-User-Id": "123"}
        )
        assert status_response.status_code == 200
        status_payload = status_response.json()
        assert status_payload["status"] == PaymentStatus.SUCCEEDED.value
        assert status_payload["provider_status"] == "succeeded"
        assert status_payload["premium"]["plan"] == "MONTHLY"
        assert status_payload["premium"]["status"] == SubscriptionStatus.ACTIVE.value
        assert status_payload["premium"]["valid_until"] is not None

        subscription_response = await client.get(
            "/billing/subscription", headers={"X-User-Id": "123"}
        )
        assert subscription_response.status_code == 200
        subscription_payload = subscription_response.json()
        assert subscription_payload["active"] is True
        assert subscription_payload["plan"] == "MONTHLY"
        assert subscription_payload["until"] is not None

        async_sessionmaker = session_factory
        async with async_sessionmaker() as session:
            payment_rows = (await session.execute(select(Payment))).scalars().all()
            assert len(payment_rows) == 1
            assert payment_rows[0].status == PaymentStatus.SUCCEEDED

            subs = (await session.execute(select(Subscription))).scalars().all()
            assert len(subs) == 1
            assert subs[0].status == SubscriptionStatus.ACTIVE
            assert subs[0].plan_code == "MONTHLY"
    finally:
        settings.premium_enabled = premium_original
        settings.payment_provider = provider_original
