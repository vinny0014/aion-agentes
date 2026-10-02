from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.commerce.router import router, get_store
from app.commerce.store import CommerceStore
from app.core.config import settings
from app.core.security import require_admin


def client(tmp_path, *, admin=False):
    store=CommerceStore(tmp_path/'api.db'); store.initialize()
    app=FastAPI(); app.include_router(router)
    app.dependency_overrides[get_store]=lambda:store
    if admin:
        app.dependency_overrides[require_admin]=lambda:{'id':1,'role':'admin'}
    return TestClient(app)


def offer(now=1800000000):
    return dict(product_id='1:2',title='TEST ONLY',category='casa',price_cents=1990,
        observed_at=now-10,expires_at=now+1800,
        affiliate_url='https://shope.ee/fixture?x=A%2FB&x=2',
        source_url='https://shopee.com.br/product/1/2',
        image_url='https://down-br.img.susercontent.com/file/fixture',
        image_source='shopee',source='shopee_official_export')


def test_catalog_is_empty_and_admin_requires_auth(tmp_path):
    c=client(tmp_path)
    assert c.get('/api/commerce/catalog').json()['items']==[]
    assert c.get('/api/commerce/admin').status_code==401
    assert c.post('/api/commerce/admin/import',json={}).status_code==401


def test_client_cannot_approve_or_forge_financial_events(tmp_path):
    c=client(tmp_path)
    for event in ['commission_approved','order','shopee_attributed_click']:
        assert c.post('/api/commerce/events',json={'event_id':'12345678-1234-1234-1234-123456789012',
            'event_type':event,'consent':True}).status_code==422
    assert c.post('/api/commerce/checks',json={'status':'VALID'}).status_code==404
    assert c.post('/api/commerce/events',json={'event_id':'12345678-1234-1234-1234-123456789012',
        'event_type':'landing_view','consent':False}).status_code==422


def test_feature_disabled_without_explicit_enable(monkeypatch):
    monkeypatch.setattr(settings,'COMPRAPULSE_ENABLED',False)
    app=FastAPI(); app.include_router(router)
    assert TestClient(app).get('/api/commerce/catalog').status_code==503


def test_admin_import_requires_receipt_from_matching_preview(tmp_path,monkeypatch):
    now=1800000000
    monkeypatch.setattr('app.commerce.importers.time.time',lambda:now)
    monkeypatch.setattr('app.commerce.router.time.time',lambda:now)
    c=client(tmp_path,admin=True)
    record=offer(now)

    preview=c.post('/api/commerce/admin/import/preview',json={'records':[record]})
    assert preview.status_code==200
    body=preview.json()
    assert body['accepted_count']==1 and body['persisted'] is False
    receipt=body['preview_receipts'][0]['receipt']
    assert 'shopee.com.br' not in receipt and 'shope.ee' not in receipt

    assert c.post('/api/commerce/admin/import',json=record).status_code==422
    saved=c.post('/api/commerce/admin/import',json={
        'record':record,'preview_receipt':receipt})
    assert saved.status_code==201 and saved.json()['created'] is True

    changed=dict(record,price_cents=record['price_cents']+1)
    assert c.post('/api/commerce/admin/import',json={
        'record':changed,'preview_receipt':receipt}).status_code==422
