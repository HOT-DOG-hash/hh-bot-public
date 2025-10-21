from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Mapping
from datetime import datetime
from typing import Any

import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.secrets import read_secret
from backend.app.payments.base import PaymentInvoice, PaymentProviderError, PaymentStatus

USER_AGENT = "HHOfferBot/1.0"
MAX_ATTEMPTS = 5
BASE_BACKOFF_SECONDS = 0.1
CIRCUIT_FAILURE_THRESHOLD = 5
MAX_CIRCUIT_SECONDS = 30.0


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _cleanup_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    result: dict[str, Any] = {}
    for key, value in metadata.items():
        result[str(key)] = value
    return result


class YooMoneyProvider:
    def __init__(self) -> None:
        self._client_id = read_secret("yoomoney_client_id", env_fallback="YOOMONEY_CLIENT_ID")
        self._client_secret = read_secret(
            "yoomoney_client_secret", env_fallback="YOOMONEY_CLIENT_SECRET"
        )
        self._base_url = settings.yoomoney_api_base.rstrip("/")
        self._timeout = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)
        self._failure_count = 0
        self._circuit_open_until = 0.0

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            auth=(self._client_id, self._client_secret),
            headers={"User-Agent": USER_AGENT},
        )

    async def create_invoice(
        self,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        *,
        idempotence_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentInvoice:
        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": currency},
            "description": description[:128],
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": return_url},
            "metadata": _cleanup_metadata(metadata),
        }
        headers: dict[str, str] = {}
        if idempotence_key:
            headers["Idempotence-Key"] = idempotence_key

        async with self._client() as client:
            response_json = await self._request(
                client,
                method="POST",
                path="/payments",
                json_payload=payload,
                headers=headers,
                action="create_payment",
            )

        confirmation = response_json.get("confirmation") or {}
        confirmation_url = confirmation.get("confirmation_url") or return_url

        return PaymentInvoice(
            external_id=response_json.get("id", ""),
            confirmation_url=confirmation_url,
            status=str(response_json.get("status", "created")),
            created_at=_parse_dt(response_json.get("created_at")),
            raw=response_json,
        )

    async def get_status(self, external_id: str) -> PaymentStatus:
        async with self._client() as client:
            response_json = await self._request(
                client,
                method="GET",
                path=f"/payments/{external_id}",
                action="get_status",
            )

        status = str(response_json.get("status", "unknown"))
        paid_at = _parse_dt(response_json.get("captured_at") or response_json.get("paid_at"))
        return PaymentStatus(
            external_id=response_json.get("id", external_id),
            status=status,
            paid_at=paid_at,
            raw=response_json,
        )

    async def _request(
        self,
        client: httpx.AsyncClient,
        *,
        method: str,
        path: str,
        action: str,
        json_payload: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        now = time.monotonic()
        if now < self._circuit_open_until:
            raise PaymentProviderError("Платёжный провайдер временно недоступен")

        last_error: Exception | None = None
        extra_headers = dict(headers or {})

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await client.request(
                    method,
                    path,
                    json=json_payload,
                    headers=extra_headers,
                )
                if response.status_code == 409 and response.headers.get("Location"):
                    location = response.headers["Location"]
                    response = await client.get(location)

                response.raise_for_status()
                self._failure_count = 0
                return response.json()
            except httpx.TimeoutException as exc:
                last_error = exc
                self._failure_count += 1
                logger.warning("yoomoney_timeout", action=action, attempt=attempt)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status_code = exc.response.status_code
                if 500 <= status_code < 600 and attempt < MAX_ATTEMPTS:
                    self._failure_count += 1
                    logger.warning(
                        "yoomoney_http_retry", action=action, status=status_code, attempt=attempt
                    )
                else:
                    detail = _safe_json(exc.response)
                    logger.warning("yoomoney_http_error", action=action, status=status_code)
                    self._failure_count = 0
                    raise PaymentProviderError(
                        "Ошибка платёжного провайдера",
                        status_code=status_code,
                        payload=detail,
                    ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                self._failure_count += 1
                logger.warning("yoomoney_transport_error", action=action, attempt=attempt)

            backoff = min(MAX_CIRCUIT_SECONDS, BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))
            await asyncio.sleep(backoff)

        self._open_circuit()
        raise PaymentProviderError("Платёжный провайдер не ответил вовремя") from last_error

    def _open_circuit(self) -> None:
        if self._failure_count >= CIRCUIT_FAILURE_THRESHOLD:
            cooldown = min(MAX_CIRCUIT_SECONDS, BASE_BACKOFF_SECONDS * (2**self._failure_count))
            self._circuit_open_until = time.monotonic() + cooldown
            logger.warning("yoomoney_circuit_open", cooldown=cooldown, failures=self._failure_count)
        else:
            self._circuit_open_until = 0.0


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        return response.text


_PROVIDER: YooMoneyProvider | None = None


def _get_provider() -> YooMoneyProvider:
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = YooMoneyProvider()
    return _PROVIDER


async def create_payment(
    amount_rub: float,
    description: str,
    return_url: str,
    *,
    idempotence_key: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> PaymentInvoice:
    provider = _get_provider()
    return await provider.create_invoice(
        amount=amount_rub,
        currency="RUB",
        description=description,
        return_url=return_url,
        idempotence_key=idempotence_key,
        metadata=metadata,
    )


async def get_payment_status(external_id: str) -> PaymentStatus:
    provider = _get_provider()
    return await provider.get_status(external_id)
