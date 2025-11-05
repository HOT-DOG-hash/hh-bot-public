from __future__ import annotations

from typing import Any, Dict, List, cast

from httpx import AsyncClient, HTTPStatusError


class BackendApiError(RuntimeError):
    pass


class BackendApi:
    """
    Thin async wrapper around the FastAPI app so that the Telegram bot always
    interacts with public HTTP endpoints instead of bypassing them.
    """

    def __init__(self, client: AsyncClient):
        self._client = client

    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        response = await self._client.request(method, url, **kwargs)
        try:
            response.raise_for_status()
        except HTTPStatusError as exc:  # pragma: no cover - httpx already tested
            detail = response.json().get("detail") if response.headers.get("content-type") else None
            raise BackendApiError(detail or str(exc)) from exc
        if response.headers.get("content-type", "").startswith("application/json"):
            return cast(Dict[str, Any], response.json())
        return {}

    async def get_plans(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/api/v1/billing/plans")
        return cast(List[Dict[str, Any]], data.get("plans", []))

    async def activate_trial(self, identity: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"plan_code": "FREE_TRIAL", **identity}
        return await self._request("POST", "/api/v1/billing/trial/activate", json=payload)

    async def get_subscription(self, identity: Dict[str, Any]) -> Dict[str, Any]:
        params = {"telegram_id": identity["telegram_id"]}
        return await self._request("GET", "/api/v1/billing/subscription", params=params)

    async def get_quota(self, identity: Dict[str, Any]) -> Dict[str, Any]:
        params = {"telegram_id": identity["telegram_id"]}
        return await self._request("GET", "/api/v1/quota", params=params)

    async def consume_quota(self, identity: Dict[str, Any], count: int) -> Dict[str, Any]:
        payload = {"count": count, **identity}
        return await self._request("POST", "/api/v1/quota/consume", json=payload)

    async def initiate_payment(self, identity: Dict[str, Any], plan_code: str, idempotency_key: str) -> Dict[str, Any]:
        payload = {
            "telegram_id": identity["telegram_id"],
            "plan_code": plan_code,
            "idempotency_key": idempotency_key,
        }
        return await self._request("POST", "/api/v1/payments/initiate", json=payload)
