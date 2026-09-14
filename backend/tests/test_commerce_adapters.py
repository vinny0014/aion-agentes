import pytest

from app.commerce.adapters import (
    AdapterBatch,
    AdapterUnavailable,
    DisabledShopeeAdapter,
    bounded_batch,
)


def test_disabled_shopee_adapter_is_fail_closed():
    adapter = DisabledShopeeAdapter()
    with pytest.raises(AdapterUnavailable, match="official_shopee_adapter_not_configured"):
        adapter.fetch_offers(limit=10)


class FixtureAdapter:
    source_name = "fixture_official"

    def __init__(self, records=(), source=None):
        self.records = tuple(records)
        self.source = source or self.source_name

    def fetch_offers(self, *, limit):
        return AdapterBatch(self.source, self.records)


def test_bounded_batch_accepts_matching_official_source_without_exposing_policy():
    records = ({"product_id": "1:2"}, {"product_id": "3:4"})
    batch = bounded_batch(FixtureAdapter(records), limit=2)
    assert batch.records == records
    assert batch.source == "fixture_official"


def test_bounded_batch_rejects_limits_source_mismatch_and_oversized_results():
    with pytest.raises(ValueError, match="adapter_limit_exceeded"):
        bounded_batch(FixtureAdapter(), limit=501)
    with pytest.raises(ValueError, match="adapter_source_mismatch"):
        bounded_batch(FixtureAdapter(source="other"), limit=1)
    with pytest.raises(ValueError, match="adapter_batch_limit_exceeded"):
        bounded_batch(FixtureAdapter(({}, {})), limit=1)


def test_disabled_adapter_rejects_invalid_limit_before_any_provider_work():
    adapter = DisabledShopeeAdapter()
    for limit in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="invalid_adapter_limit"):
            adapter.fetch_offers(limit=limit)
