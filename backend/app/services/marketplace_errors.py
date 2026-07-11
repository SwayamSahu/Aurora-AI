"""Shared exception types for the marketplace domain (wallet/plans now,
listings/cart/checkout in later phases). Routes catch these and translate
to the appropriate HTTP status."""

from __future__ import annotations


class MarketplaceError(Exception):
    """Base class for marketplace domain errors."""


class InsufficientCreditsError(MarketplaceError):
    pass


class QuotaExceededError(MarketplaceError):
    pass


class ListingUnavailableError(MarketplaceError):
    pass


class PaymentFailedError(MarketplaceError):
    pass


class RateLimitedError(MarketplaceError):
    pass
