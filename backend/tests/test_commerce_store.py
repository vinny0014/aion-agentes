"""All commercial data below are isolated test fixtures, never production seeds."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.commerce.store import CommerceStore
from app.commerce.guardrails import validate_shopee_url_structure, LinkStatus
from app.commerce.jobs import schedule, run_once, enqueue_publish_candidates
from app.commerce.scoring import pulse_score
NOW=1800000000

@pytest.fixture
def store(tmp_path):
    s=CommerceStore(tmp_path/'test.db'); s.initialize(); return s

def offer():
    return dict(product_id='1:2',title='TEST ONLY',category='casa',price_cents=1990,
        observed_at=NOW-10,expires_at=NOW+1800,affiliate_url='https://shope.ee/fixture?x=A%2FB&x=2',
        source_url='https://shopee.com.br/product/1/2',image_url='https://down-br.img.susercontent.com/file/fixture',
        image_source='shopee',source='shopee_official_export')

def verify(s,oid,**changes):
    with s.transaction() as c:
        r=c.execute('SELECT * FROM cp_offers WHERE id=?',(oid,)).fetchone()
    args=dict(status='VALID',destination_product_id=r['product_id'],image_valid=True,
        stock_valid=True,official_provenance=True,tracking_verified=True,evidence_ref='test-fixture',
        checked_at=NOW,expires_at=NOW+600,input_hash=r['input_hash'],now=NOW)
    from app.commerce.scoring import WEIGHTS
    s.record_score(oid,{key:90 for key in WEIGHTS},evidence_ref='test-fixture',now=NOW)
    args.update(changes); s.record_check(oid,**args)

def test_import_replay_exact_link_draft(store):
    first=store.ingest(offer(),NOW); second=store.ingest(offer(),NOW)
    assert first['created'] and not second['created']
    assert first['offer_id']==second['offer_id']
    assert not store.publish(first['offer_id'],now=NOW)
    with store.transaction() as c:
        assert c.execute('SELECT affiliate_url_exact FROM cp_offers').fetchone()[0]==offer()['affiliate_url']
        assert c.execute('SELECT COUNT(*) FROM cp_price_history').fetchone()[0]==1

def test_expiration_without_scheduler(store):
    oid=store.ingest(offer(),NOW)['offer_id']; verify(store,oid)
    assert store.publish(oid,now=NOW) and len(store.catalog(NOW))==1
    assert not store.catalog(NOW+600)
    with store.transaction() as c:
        assert c.execute('SELECT status FROM cp_offers').fetchone()[0]=='paused'

@pytest.mark.parametrize('change',[{'image_valid':False},{'stock_valid':False},
    {'tracking_verified':False},{'official_provenance':False},{'destination_product_id':'other'},
    {'status':'UNKNOWN'},{'status':'MISMATCH'},{'status':'REVIEW_REQUIRED'}])
def test_failed_signals_block(store,change):
    oid=store.ingest(offer(),NOW)['offer_id']; verify(store,oid,**change)
    assert not store.publish(oid,now=NOW)

def test_new_link_revokes_old_validation(store):
    oid=store.ingest(offer(),NOW)['offer_id']; verify(store,oid); store.publish(oid,now=NOW)
    updated=offer(); updated.update(affiliate_url='https://shope.ee/new',observed_at=NOW)
    new=store.ingest(updated,NOW)['offer_id']
    assert new!=oid and not store.catalog(NOW)
    assert not store.publish(oid,now=NOW) and not store.publish(new,now=NOW)
    assert not store.ingest(offer(),NOW)['created']
    assert not store.catalog(NOW)

def test_bad_import_atomic(store):
    p=offer(); p['price_cents']=True
    with pytest.raises(ValueError): store.ingest(p,NOW)
    with store.transaction() as c:
        assert c.execute('SELECT COUNT(*) FROM cp_products').fetchone()[0]==0

def test_jobs_exclusive_claim_and_stale_worker(store):
    jid=store.enqueue('refresh_offer','1','hash',1,NOW)
    assert jid==store.enqueue('refresh_offer','1','hash',1,NOW)
    with ThreadPoolExecutor(2) as pool:
        claimed=list(pool.map(lambda _:store.claim(NOW),range(2)))
    old=next(r for r in claimed if r)
    assert sum(r is not None for r in claimed)==1
    newer=store.claim(NOW+121)
    assert not store.finish(jid,old['lease_token'],now=NOW+122)
    assert store.finish(jid,newer['lease_token'],now=NOW+122)
    assert store.claim(NOW+300) is None

def test_retry_backoff_exhaustion(store):
    jid=store.enqueue('refresh_offer','1','hash',1,NOW)
    for n in range(3):
        at=NOW+n*1000; j=store.claim(at)
        assert j['attempt']==n+1
        store.finish(jid,j['lease_token'],error_code='timeout',now=at)
        assert store.claim(at) is None
    assert store.claim(NOW+10000) is None

def test_missing_adapter_is_blocked_not_success(store):
    schedule(store,NOW); schedule(store,NOW)
    assert run_once(store,now=NOW)=='blocked'
    assert run_once(store,now=NOW) is None

def test_hourly_publication_budget_is_atomic_and_fail_closed(store):
    ids=[]
    for i in range(12):
        p=offer(); p['product_id']=f'1:{i+10}'; p['source_url']=f'https://shopee.com.br/product/1/{i+10}'
        oid=store.ingest(p,NOW)['offer_id']; verify(store,oid); ids.append(oid)
    first=enqueue_publish_candidates(store,ids,now=NOW)
    second=enqueue_publish_candidates(store,list(reversed(ids)),now=NOW)
    assert len(first)==10 and second==[]
    assert [run_once(store,now=NOW) for _ in range(10)]==['done']*10
    assert run_once(store,now=NOW) is None
    assert len(store.catalog(NOW))==10
    with store.transaction() as c:
        assert c.execute("SELECT COUNT(*) FROM cp_jobs WHERE job_type='publish_offer' AND cycle=?",(NOW//3600,)).fetchone()[0]==10
        assert c.execute("SELECT COUNT(*) FROM cp_offers WHERE status='active'").fetchone()[0]==10

def test_click_is_not_commission(store):
    oid=store.ingest(offer(),NOW)['offer_id']; verify(store,oid); store.publish(oid,now=NOW)
    store.record_event('unique','merchant_click',offer_id=oid,now=NOW)
    store.record_event('unique','merchant_click',offer_id=oid,now=NOW)
    with pytest.raises(ValueError): store.record_event('fake','commission_approved',now=NOW)
    m=store.metrics()
    assert m['events']['merchant_click']==1 and m['approved_commission_cents']==0
    assert m['shopee_attributed_clicks'] is None and m['orders'] is None
    with pytest.raises(ValueError): store.record_event('late','merchant_click',offer_id=oid,now=NOW+600)

@pytest.mark.parametrize('url',[' https://shopee.com.br/a','https://u:p@shopee.com.br/a',
    'https://shopee.com.br:123/a','https://shopee.com.br:bad/a','https://shopee.com.br\\@evil.com/a',
    'https://shopee.com.br/a\n','https://shopee.com.br.evil.com/a'])
def test_ambiguous_urls(url):
    assert validate_shopee_url_structure(url).status==LinkStatus.INVALID

def test_score_missing_evidence():
    r=pulse_score({'commission':100})
    assert r['score']==10 and not r['eligible'] and r['missing']
    with pytest.raises(ValueError): pulse_score({'rating':float('nan')})
