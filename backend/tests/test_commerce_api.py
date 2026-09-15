from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.commerce.router import router, get_store
from app.commerce.store import CommerceStore
from app.core.config import settings


def client(tmp_path):
    store=CommerceStore(tmp_path/'api.db'); store.initialize()
    app=FastAPI(); app.include_router(router)
    app.dependency_overrides[get_store]=lambda:store
    return TestClient(app)


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
