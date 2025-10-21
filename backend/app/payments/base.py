from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass(slots=True)
class PaymentInvoice:
    external_id: str
    confirmation_url: str
    status: str
    created_at: datetime | None
    raw: dict[str, Any]


@dataclass(slots=True)
class PaymentStatus:
    external_id: str
    status: str
    paid_at: datetime | None
    raw: dict[str, Any]


class PaymentProviderError(RuntimeError):
    """Базовая ошибка платёжного провайдера."""

    def __init__(
        self, message: str, *, status_code: int | None = None, payload: Any | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class PaymentProvider(Protocol):
    async def create_invoice(
        self,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        *,
        idempotence_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentInvoice: ...

    async def get_status(self, external_id: str) -> PaymentStatus: ...


__all__ = [
    "PaymentInvoice",
    "PaymentStatus",
    "PaymentProvider",
    "PaymentProviderError",
]
