import csv

import pytest

from app.commerce.adapters import (
    AdapterBatch,
    AdapterUnavailable,
    DisabledShopeeAdapter,
    ShopeeOfficialCsvAdapter,
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


EXPORT_FIELDS = [
    "shop_rating", "itemid", "sale_price", "item_rating", "global_category3",
    "cb_option", "discount_percentage", "global_catid2", "price", "description",
    "title", "global_category1", "image_link_3", "global_catid1", "global_catid3",
    "like", "condition", "global_category2", "model_ids", "image_link",
    "model_names", "shop_name", "product_link", "product_short link",
]


def export_row(item_id="19297679987"):
    product = f"https://shopee.com.br/product/398944029/{item_id}"
    return {
        "itemid": item_id,
        "sale_price": "147.02",
        "title": "TEST ONLY official feed fixture",
        "global_category1": "Pets",
        "global_category2": "Pet Food",
        "global_category3": "Cat Food",
        "image_link": "https://cf.shopee.com.br/file/test-fixture",
        "product_link": product,
        "product_short link": "https://shope.ee/an_redir?origin_link="
        + product.replace(":", "%3A").replace("/", "%2F"),
    }


def write_export(tmp_path, rows, fields=EXPORT_FIELDS):
    path = tmp_path / "official.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def test_official_csv_adapter_streams_exact_observed_schema(tmp_path):
    path = write_export(tmp_path, [export_row(), export_row("55557474043")])
    adapter = ShopeeOfficialCsvAdapter(path, observed_at=1800000000, ttl_seconds=3600)

    batch = bounded_batch(adapter, limit=1)

    assert batch.source == "shopee_official_export"
    assert len(batch.records) == 1
    assert batch.records[0] == {
        "product_id": "398944029:19297679987",
        "title": "TEST ONLY official feed fixture",
        "category": "Cat Food",
        "price_cents": 14702,
        "observed_at": 1800000000,
        "expires_at": 1800003600,
        "affiliate_url": "https://shope.ee/an_redir?origin_link=https%3A%2F%2Fshopee.com.br%2Fproduct%2F398944029%2F19297679987",
        "source_url": "https://shopee.com.br/product/398944029/19297679987",
        "image_url": "https://cf.shopee.com.br/file/test-fixture",
        "image_source": "shopee_official_export",
        "source": "shopee_official_export",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sale_price", "0"),
        ("sale_price", "1.001"),
        ("itemid", "not-a-number"),
        ("product_link", "https://shopee.com.br/product/398944029/other"),
        ("product_short link", "https://shope.ee/not-the-export-redirect"),
        ("image_link", "http://cf.shopee.com.br/file/test-fixture"),
    ],
)
def test_official_csv_adapter_rejects_malformed_commercial_records(tmp_path, field, value):
    row = export_row()
    row[field] = value
    adapter = ShopeeOfficialCsvAdapter(write_export(tmp_path, [row]), observed_at=1800000000)

    with pytest.raises(ValueError, match="invalid_export_record"):
        adapter.fetch_offers(limit=1)


def test_official_csv_adapter_rejects_unknown_schema_and_invalid_timestamps(tmp_path):
    path = write_export(
        tmp_path,
        [{"itemid": "19297679987", "title": "TEST ONLY"}],
        fields=["itemid", "title"],
    )
    with pytest.raises(ValueError, match="invalid_official_export_schema"):
        ShopeeOfficialCsvAdapter(path, observed_at=1800000000).fetch_offers(limit=1)

    for observed_at in (0, True, 1.5):
        with pytest.raises(ValueError, match="invalid_export_observed_at"):
            ShopeeOfficialCsvAdapter(path, observed_at=observed_at)
