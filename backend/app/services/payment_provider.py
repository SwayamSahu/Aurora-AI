"""Swappable payment backend — same pattern as `app/storage.py`'s
`get_storage()` and the generator registry: one interface, a cached
singleton factory, and a mock implementation that's the default everywhere
until real payment credentials are configured.

`MockPaymentProvider` always succeeds instantly and is the ACTIVE provider
in this build (no `STRIPE_SECRET_KEY` is configured anywhere in this
environment). `StripePaymentProvider` below is a structural scaffold only —
see its docstring for exactly what's unverified before it's production-ready.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

import httpx

from app.core.config import settings


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


class StripePaymentProvider(PaymentProvider):
    """Real Stripe charges via the REST API — SCAFFOLDED, NOT VERIFIED.

    This was built without a Stripe account to test against (see the M7
    decision log). It is structurally correct against Stripe's documented
    PaymentIntents API, but has real gaps before it's production-ready:

    1. No card-collection UI exists in this app yet, so this hardcodes
       Stripe's official TEST-mode PaymentMethod token (`pm_card_visa`)
       instead of accepting a real one from the client. In Stripe's live
       mode, confirming a PaymentIntent with a test token fails cleanly
       (Stripe rejects it) — so this cannot accidentally charge a real
       card, but it also cannot charge one on purpose yet.
    2. Before going live: add a client-side Stripe Elements/Checkout flow
       to collect a real payment method and thread its id through
       `charge()` in place of the hardcoded token.
    3. This assumes synchronous confirmation succeeds or fails immediately.
       Real cards can require asynchronous steps (3D Secure/SCA) that need
       a webhook handler to resolve — none exists in this build.
    4. Never actually exercised against Stripe's API (no test keys were
       available), so even the "structurally correct" claim above is
       unverified — read the Stripe PaymentIntents docs and test against a
       real test-mode account before trusting this in any real flow.
    """

    name = "stripe"

    def __init__(self) -> None:
        if not settings.stripe_secret_key:
            raise RuntimeError("STRIPE_SECRET_KEY is not configured.")
        self._api_key = settings.stripe_secret_key

    def charge(
        self, *, user_id: str, amount_cents: int, description: str
    ) -> ChargeResult:
        if amount_cents <= 0:
            return ChargeResult(success=True, provider_ref="stripe_free")

        try:
            res = httpx.post(
                "https://api.stripe.com/v1/payment_intents",
                auth=(self._api_key, ""),
                data={
                    "amount": amount_cents,
                    "currency": "usd",
                    "description": description,
                    "payment_method": "pm_card_visa",  # TEST-MODE ONLY — see class docstring
                    "confirm": "true",
                    "off_session": "true",
                    "metadata[user_id]": user_id,
                },
                timeout=15.0,
            )
            data = res.json()
        except httpx.HTTPError as exc:
            return ChargeResult(success=False, provider_ref="", failure_reason=str(exc))

        if res.status_code >= 400:
            error = data.get("error", {})
            return ChargeResult(
                success=False,
                provider_ref=error.get("payment_intent", {}).get("id", ""),
                failure_reason=error.get("message", "Stripe charge failed."),
            )
        if data.get("status") != "succeeded":
            return ChargeResult(
                success=False,
                provider_ref=data.get("id", ""),
                failure_reason=f"Unexpected PaymentIntent status: {data.get('status')}",
            )
        return ChargeResult(success=True, provider_ref=data["id"])


@lru_cache
def get_payment_provider() -> PaymentProvider:
    if settings.stripe_secret_key:
        return StripePaymentProvider()
    return MockPaymentProvider()
