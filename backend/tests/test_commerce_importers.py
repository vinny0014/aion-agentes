import pytest

from app.commerce.adapters import AdapterBatch
from app.commerce.importers import (
    MAX_PREVIEW_RECORDS,
    preview_adapter_records,
    preview_official_records,
)

NOW = 1800000000


def offer():
    return dict(product_id='1:2',title='TEST ONLY',category='casa',price_cents=1990,
        observed_at=NOW-10,expires_at=NOW+1800,
        affiliate_url='https://shope.ee/fixture?x=A%2FB&x=2',
        source_url='https://shopee.com.br/product/1/2',
        image_url='https://down-br.img.susercontent.com/file/fixture',
        image_source='shopee',source='shopee_official_export')


class OfficialFixtureAdapter:
    source_name = 'shopee_official_export'

    def __init__(self, records):
        self.records = tuple(records)

    def fetch_offers(self, *, limit):
        return AdapterBatch(self.source_name, self.records)


class UnknownSourceAdapter(OfficialFixtureAdapter):
    source_name = 'fixture_untrusted_source'


def test_preview_is_side_effect_free_and_does_not_echo_urls():
    bad=offer(); bad['price_cents']=0
    result=preview_official_records([offer(),bad],now=NOW)
    assert result['total']==2
    assert result['accepted_indexes']==[0]
    assert result['rejected_count']==1
    assert result['persisted'] is False and result['published'] is False
    rendered=str(result)
    assert 'shopee.com.br' not in rendered and 'shope.ee' not in rendered


def test_preview_rejects_non_list_and_oversized_batches():
    for records in ({},None,'records'):
        try:
            preview_official_records(records,now=NOW)
            assert False, 'expected ValueError'
        except ValueError:
            pass
    try:
        preview_official_records([offer()]*(MAX_PREVIEW_RECORDS+1),now=NOW)
        assert False, 'expected ValueError'
    except ValueError as exc:
        assert str(exc)=='preview_limit_exceeded'


def test_preview_rejects_unknown_fields_without_leaking_values():
    record=offer(); record['secret_token']='do-not-echo-me'
    result=preview_official_records([record],now=NOW)
    assert result['accepted_count']==0
    assert result['rejected'][0]['error_code']=='invalid_offer_fields'
    assert 'do-not-echo-me' not in str(result)


def test_adapter_preview_binds_batch_and_record_to_same_official_source():
    result=preview_adapter_records(OfficialFixtureAdapter([offer()]),limit=1,now=NOW)
    assert result['accepted_count']==1
    assert result['source']=='shopee_official_export'
    assert result['persisted'] is False and result['published'] is False
    assert 'shope.ee' not in str(result)


def test_adapter_preview_rejects_unknown_or_mixed_provenance_fail_closed():
    with pytest.raises(ValueError,match='unsupported_official_source'):
        preview_adapter_records(UnknownSourceAdapter([offer()]),limit=1,now=NOW)

    mismatched=offer(); mismatched['source']='shopee_official_api'
    with pytest.raises(ValueError,match='adapter_record_source_mismatch'):
        preview_adapter_records(OfficialFixtureAdapter([mismatched]),limit=1,now=NOW)
