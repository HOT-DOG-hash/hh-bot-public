from __future__ import annotations

import pytest
from sqlalchemy import select

from backend.app.core.db import get_session_factory
from backend.app.models.payments import Payment, PaymentAttempt, PaymentStatus
from backend.tests.payments.helpers import create_user


@pytest.mark.asyncio
async def test_payment_initiation_idempotent(client):
    user_id = await create_user()
    payload = {
        "user_id": user_id,
        "plan_code": "WEEKLY",
        "idempotency_key": "idem-weekly-1",
    }

    response_one = await client.post("/api/v1/payments/initiate", json=payload)
    assert response_one.status_code == 200
    data_one = response_one.json()
    assert data_one["status"] == PaymentStatus.INITIATED.value
    assert data_one["invoice_url"]

    response_two = await client.post("/api/v1/payments/initiate", json=payload)
    assert response_two.status_code == 200
    data_two = response_two.json()
    assert data_two == data_one

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(Payment).where(Payment.user_id == user_id))
        payments = result.scalars().all()
        assert len(payments) == 1
        payment = payments[0]
        assert payment.status is PaymentStatus.INITIATED

        attempt_result = await session.execute(
            select(PaymentAttempt).where(PaymentAttempt.payment_id == payment.id)
        )
        attempts = attempt_result.scalars().all()
        assert len(attempts) == 1

    metrics_resp = await client.get("/metrics")
    assert metrics_resp.status_code == 200
    lines = [line for line in metrics_resp.text.splitlines() if line.startswith('payments_initiated_total')]
    assert any('{plan_code="WEEKLY"}' in line for line in lines)
