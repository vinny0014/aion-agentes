"""Fail-closed contract for authorized Shopee offer sources.

Adapters translate an authorized official source (API/export) into normalized
records. This module intentionally performs no network access and stores no
credentials. Real provider implementations must be added only after authorized
access is available.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable
from urllib.parse import parse_qs, unquote, urlsplit


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


class ShopeeOfficialCsvAdapter:
    """Stream the authenticated Shopee product-feed CSV without side effects.

    The export provides a Shopee redirect URL, but the presence of that URL does
    not prove attribution. Records produced here remain drafts and still require
    the independent link, image, stock and tracking evidence used by the
    publication guardrails.
    """

    source_name = "shopee_official_export"
    required_columns = frozenset(
        {
            "itemid",
            "sale_price",
            "title",
            "global_category1",
            "global_category2",
            "global_category3",
            "image_link",
            "product_link",
            "product_short link",
        }
    )

    def __init__(self, path: str | Path, *, observed_at: int, ttl_seconds: int = 86400):
        if type(observed_at) is not int or observed_at < 1:
            raise ValueError("invalid_export_observed_at")
        if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 86400:
            raise ValueError("invalid_export_ttl")
        self.path = Path(path)
        self.observed_at = observed_at
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def _price_cents(value: str) -> int:
        try:
            price = Decimal(value)
        except (InvalidOperation, TypeError):
            raise ValueError("invalid_export_record") from None
        if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
            raise ValueError("invalid_export_record")
        cents = price * 100
        if cents != cents.to_integral_value() or cents > 10**12:
            raise ValueError("invalid_export_record")
        return int(cents)

    @staticmethod
    def _product_identity(product_url: str, item_id: str) -> str:
        try:
            parsed = urlsplit(product_url)
        except ValueError:
            raise ValueError("invalid_export_record") from None
        host = (parsed.hostname or "").lower().rstrip(".")
        parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.scheme != "https"
            or host != "shopee.com.br"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or len(parts) != 3
            or parts[0] != "product"
            or not parts[1].isdigit()
            or not parts[2].isdigit()
            or parts[2] != item_id
        ):
            raise ValueError("invalid_export_record")
        return f"{parts[1]}:{parts[2]}"

    @staticmethod
    def _affiliate_matches_product(affiliate_url: str, product_url: str) -> None:
        try:
            parsed = urlsplit(affiliate_url)
            query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
        except ValueError:
            raise ValueError("invalid_export_record") from None
        origins = query.get("origin_link", [])
        if (
            parsed.scheme != "https"
            or (parsed.hostname or "").lower().rstrip(".") != "shope.ee"
            or parsed.username
            or parsed.password
            or parsed.path != "/an_redir"
            or len(origins) != 1
            or unquote(origins[0]) != product_url
        ):
            raise ValueError("invalid_export_record")

    def _map_record(self, row: Mapping[str, str | None]) -> Mapping[str, Any]:
        def field(name: str, maximum: int = 4096) -> str:
            value = row.get(name)
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > maximum:
                raise ValueError("invalid_export_record")
            return value

        item_id = field("itemid", 32)
        if not item_id.isdigit():
            raise ValueError("invalid_export_record")
        source_url = field("product_link")
        product_id = self._product_identity(source_url, item_id)
        affiliate_url = field("product_short link")
        self._affiliate_matches_product(affiliate_url, source_url)

        image_url = field("image_link")
        image = urlsplit(image_url)
        if image.scheme != "https" or not image.hostname or image.username or image.password:
            raise ValueError("invalid_export_record")

        category = next(
            (
                value.strip()
                for name in ("global_category3", "global_category2", "global_category1")
                if isinstance((value := row.get(name)), str) and value.strip()
            ),
            None,
        )
        if not category or len(category) > 200:
            raise ValueError("invalid_export_record")

        return {
            "product_id": product_id,
            "title": field("title", 200),
            "category": category,
            "price_cents": self._price_cents(field("sale_price", 32)),
            "observed_at": self.observed_at,
            "expires_at": self.observed_at + self.ttl_seconds,
            "affiliate_url": affiliate_url,
            "source_url": source_url,
            "image_url": image_url,
            "image_source": self.source_name,
            "source": self.source_name,
        }

    def fetch_offers(self, *, limit: int) -> AdapterBatch:
        if type(limit) is not int or limit < 1:
            raise ValueError("invalid_adapter_limit")
        try:
            with self.path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                columns = reader.fieldnames
                if (
                    not columns
                    or len(columns) != len(set(columns))
                    or not self.required_columns.issubset(columns)
                ):
                    raise ValueError("invalid_official_export_schema")
                records = []
                for row in reader:
                    if len(records) == limit:
                        break
                    records.append(self._map_record(row))
        except (OSError, UnicodeError, csv.Error) as exc:
            raise AdapterUnavailable("official_shopee_export_unavailable") from exc
        return AdapterBatch(self.source_name, tuple(records))


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
