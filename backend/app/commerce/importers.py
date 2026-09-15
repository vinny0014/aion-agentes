"""Safe preview utilities for future official Shopee exports/API records.

This module never publishes, approves affiliate links, or persists data. It exists
so an authorized official export can be mapped and validated before ingestion.
"""
from __future__ import annotations

import time
from typing import Any, Mapping

from .adapters import OfficialOfferAdapter, bounded_batch
from .store import normalized_offer

MAX_PREVIEW_RECORDS = 500
ALLOWED_SHOPEE_SOURCES = frozenset(("shopee_official_export", "shopee_official_api"))


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
