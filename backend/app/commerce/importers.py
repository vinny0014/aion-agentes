"""Safe preview utilities for future official Shopee exports/API records.

This module never publishes, approves affiliate links, or persists data. It exists
so an authorized official export can be mapped and validated before ingestion.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Mapping

from .adapters import OfficialOfferAdapter, bounded_batch
from .store import normalized_offer

MAX_PREVIEW_RECORDS = 500
PREVIEW_RECEIPT_TTL_SECONDS = 300
ALLOWED_SHOPEE_SOURCES = frozenset(("shopee_official_export", "shopee_official_api"))


def _offer_digest(record: Mapping[str, Any], *, now: int) -> str:
    normalized = normalized_offer(dict(record), now)
    encoded = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def issue_preview_receipt(
    record: Mapping[str, Any], *, secret: str, now: int | None = None
) -> str:
    """Bind one accepted preview to the exact record for five minutes.

    The receipt contains only a version, expiry and SHA-256 digest. Commercial
    URLs and imported fields are never embedded in the token or server logs.
    """
    if not isinstance(secret, str) or not secret:
        raise ValueError("preview_receipt_secret_required")
    current = int(time.time()) if now is None else now
    digest = _offer_digest(record, now=current)
    expires = current + PREVIEW_RECEIPT_TTL_SECONDS
    message = f"v1.{expires}.{digest}"
    signature = hmac.new(secret.encode("utf-8"), message.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{message}.{signature}"


def verify_preview_receipt(
    record: Mapping[str, Any], receipt: str, *, secret: str, now: int | None = None
) -> None:
    """Reject missing, expired, forged or record-mismatched preview receipts."""
    if not isinstance(secret, str) or not secret:
        raise ValueError("preview_receipt_secret_required")
    if not isinstance(receipt, str) or len(receipt) > 256:
        raise ValueError("invalid_preview_receipt")
    parts = receipt.split(".")
    if len(parts) != 4 or parts[0] != "v1" or not parts[1].isdigit():
        raise ValueError("invalid_preview_receipt")
    _, expires_text, claimed_digest, claimed_signature = parts
    if len(claimed_digest) != 64 or len(claimed_signature) != 64:
        raise ValueError("invalid_preview_receipt")

    current = int(time.time()) if now is None else now
    expires = int(expires_text)
    if current >= expires or expires > current + PREVIEW_RECEIPT_TTL_SECONDS:
        raise ValueError("expired_preview_receipt")
    digest = _offer_digest(record, now=current)
    if not hmac.compare_digest(claimed_digest, digest):
        raise ValueError("preview_receipt_record_mismatch")
    message = f"v1.{expires}.{claimed_digest}"
    expected = hmac.new(
        secret.encode("utf-8"), message.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(claimed_signature, expected):
        raise ValueError("invalid_preview_receipt")


def preview_official_records(records: Any, *, now: int | None = None) -> dict:
    """Validate a bounded batch without echoing payloads or storing anything.

    Returns only indexes and sanitized validation codes. This prevents accidental
    exposure of affiliate URLs or other imported fields through admin responses.
    """
    if not isinstance(records, list):
        raise ValueError('records_list_required')
    if len(records) > MAX_PREVIEW_RECORDS:
        raise ValueError('preview_limit_exceeded')

    current = int(time.time()) if now is None else now
    accepted: list[int] = []
    rejected: list[dict[str, object]] = []

    for index, record in enumerate(records):
        try:
            normalized_offer(record, current)
            accepted.append(index)
        except (ValueError, TypeError, KeyError) as exc:
            code = str(exc) or exc.__class__.__name__.lower()
            if not code.replace('_', '').isalnum() or len(code) > 80:
                code = 'invalid_record'
            rejected.append({'index': index, 'error_code': code})

    return {
        'total': len(records),
        'accepted_count': len(accepted),
        'rejected_count': len(rejected),
        'accepted_indexes': accepted,
        'rejected': rejected,
        'persisted': False,
        'published': False,
    }


def preview_adapter_records(
    adapter: OfficialOfferAdapter, *, limit: int = 100, now: int | None = None
) -> dict:
    """Preview one bounded authorized Shopee adapter batch, fail-closed.

    The adapter identity and every record's declared source must agree. Mixed or
    unknown provenance rejects the whole batch before record validation so an
    untrusted payload cannot self-label itself as an official Shopee source.
    Exact URLs remain internal and are never returned by this function.
    """
    batch = bounded_batch(adapter, limit=limit, hard_cap=MAX_PREVIEW_RECORDS)
    if batch.source not in ALLOWED_SHOPEE_SOURCES:
        raise ValueError('unsupported_official_source')

    records = list(batch.records)
    for record in records:
        if not isinstance(record, Mapping) or record.get('source') != batch.source:
            raise ValueError('adapter_record_source_mismatch')

    result = preview_official_records(records, now=now)
    result['source'] = batch.source
    return result
