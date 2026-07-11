"""Swappable payment backend — same pattern as `app/storage.py`'s
`get_storage()` and the generator registry: one interface, a cached
singleton factory, and a mock implementation that's the default everywhere
until real payment credentials are configured.

`MockPaymentProvider` always succeeds instantly and is the only provider
wired up in this build (see decision log — real Stripe integration is a
separate later phase that needs live API keys to verify against)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class ChargeResult:
    success: bool
    provider_ref: str
    failure_reason: str | None = None


class PaymentProvider(ABC):
    name: str

    @abstractmethod
    def charge(
        self, *, user_id: str, amount_cents: int, description: str
    ) -> ChargeResult: ...


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    def charge(
        self, *, user_id: str, amount_cents: int, description: str
    ) -> ChargeResult:
        return ChargeResult(success=True, provider_ref=f"mock_{uuid.uuid4().hex[:16]}")


@lru_cache
def get_payment_provider() -> PaymentProvider:
    return MockPaymentProvider()
