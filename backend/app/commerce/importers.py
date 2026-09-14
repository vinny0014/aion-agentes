"""Safe preview utilities for future official Shopee exports/API records.

This module never publishes, approves affiliate links, or persists data. It exists
so an authorized official export can be mapped and validated before ingestion.
"""
from __future__ import annotations

import time
from typing import Any

from .store import normalized_offer

MAX_PREVIEW_RECORDS = 500


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
