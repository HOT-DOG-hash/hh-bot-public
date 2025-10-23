from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.models.billing import SubscriptionStatus
from backend.app.models.payments import PaymentStatus
from backend.app.services import billing as billing_service
from backend.app.services.billing import (
    BillingPlanNotFoundError,
    BillingProviderFailure,
    PaymentNotFoundError,
)

router = APIRouter(prefix="/billing", tags=["billing"])


def _default_return_url() -> str:
    return f"{settings.base_url_normalized}/billing/return"


def _normalize_user_token(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-User-Id is required")
    return token


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_billing_invoice(
    plan: str = Query(..., description="Код тарифного плана"),
    user_token: str = Header(..., alias="X-User-Id"),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if not settings.premium_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Премиум отключён"
        )

    user_ref = _normalize_user_token(user_token)
    try:
        result = await billing_service.create_payment(
            session,
            user_token=user_ref,
            plan_code=plan,
            return_url=_default_return_url(),
        )
    except BillingPlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестный тариф"
        ) from None
    except BillingProviderFailure as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from None

    payment = result.payment
    status_value = (
        payment.status.value if isinstance(payment.status, PaymentStatus) else str(payment.status)
    )

    return {
        "external_id": payment.provider_payment_id,
        "pay_url": result.pay_url,
        "status": status_value,
        "provider": settings.payment_provider,
    }


@router.get("/status/{external_id}")
async def billing_status(
    external_id: str,
    user_token: str = Header(..., alias="X-User-Id"),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    user_ref = _normalize_user_token(user_token)
    try:
        result = await billing_service.refresh_payment_status(
            session,
            user_token=user_ref,
            external_id=external_id,
        )
    except BillingProviderFailure as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from None
    except PaymentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Платёж не найден"
        ) from None

    payment = result.payment
    status_value = (
        payment.status.value if isinstance(payment.status, PaymentStatus) else str(payment.status)
    )

    subscription_payload: dict[str, object] | None = None
    if result.subscription:
        subscription_payload = {
            "plan": result.subscription.plan_code,
            "status": result.subscription.status.value
            if isinstance(result.subscription.status, SubscriptionStatus)
            else str(result.subscription.status),
            "valid_until": (
                result.subscription.current_period_end.isoformat()
                if result.subscription.current_period_end
                else None
            ),
        }

    return {
        "external_id": payment.provider_payment_id,
        "status": status_value,
        "provider_status": result.provider_status.status,
        "premium": subscription_payload,
    }


@router.get("/subscription")
async def subscription_status(
    user_token: str = Header(..., alias="X-User-Id"),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    user_ref = _normalize_user_token(user_token)
    subscription = await billing_service.get_subscription(session, user_token=user_ref)
    if not subscription:
        return {"active": False, "plan": None, "until": None}

    return {
        "active": subscription.status == SubscriptionStatus.ACTIVE,
        "plan": subscription.plan_code,
        "until": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    }
