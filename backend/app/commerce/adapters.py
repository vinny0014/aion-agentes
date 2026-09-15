"""Fail-closed contract for authorized Shopee offer sources.

Adapters translate an authorized official source (API/export) into normalized
records. This module intentionally performs no network access and stores no
credentials. Real provider implementations must be added only after authorized
access is available.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable


class AdapterUnavailable(RuntimeError):
    """Raised when an official source is not configured or authorized."""


@dataclass(frozen=True)
class AdapterBatch:
    """Sanitized adapter output ready for preview/normalization.

    ``records`` may contain exact affiliate URLs because it is an internal value;
    callers must never serialize this object into logs/admin responses.
    """

    source: str
    records: tuple[Mapping[str, Any], ...]


@runtime_checkable
class OfficialOfferAdapter(Protocol):
    """Minimum contract for an authorized Shopee offer source."""

    source_name: str

    def fetch_offers(self, *, limit: int) -> AdapterBatch:
        """Return at most ``limit`` official records or raise AdapterUnavailable."""


class DisabledShopeeAdapter:
    """Default provider used until an authorized Shopee source is configured."""

    source_name = "shopee_official_unconfigured"

    def fetch_offers(self, *, limit: int) -> AdapterBatch:
        if type(limit) is not int or limit < 1:
            raise ValueError("invalid_adapter_limit")
        raise AdapterUnavailable("official_shopee_adapter_not_configured")


def bounded_batch(adapter: OfficialOfferAdapter, *, limit: int, hard_cap: int = 500) -> AdapterBatch:
    """Call an adapter with a bounded result and enforce source identity.

    This protects future workers from an adapter ignoring its requested limit or
    returning a batch for a different provider. No record contents are logged.
    """
    if type(limit) is not int or type(hard_cap) is not int or limit < 1 or hard_cap < 1:
        raise ValueError("invalid_adapter_limit")
    if limit > hard_cap:
        raise ValueError("adapter_limit_exceeded")
    batch = adapter.fetch_offers(limit=limit)
    if not isinstance(batch, AdapterBatch):
        raise ValueError("invalid_adapter_batch")
    if batch.source != adapter.source_name:
        raise ValueError("adapter_source_mismatch")
    if len(batch.records) > limit:
        raise ValueError("adapter_batch_limit_exceeded")
    return batch
