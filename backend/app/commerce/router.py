"""Opt-in commerce API, reusing the existing admin authorization."""
import time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from ..core import database as db
from ..core.config import settings
from ..core.security import require_admin
from .importers import preview_official_records
from .store import CommerceStore


def get_store():
    if not settings.COMPRAPULSE_ENABLED:
        raise HTTPException(503,'CompraPulse is not enabled')
    return CommerceStore(db.DB_PATH)


router=APIRouter(prefix='/api/commerce',tags=['commerce'])


class Event(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event_id: UUID
    event_type: Literal['landing_view','category_view','product_view','merchant_click']
    offer_id: int | None=Field(default=None,ge=1)
    placement: Literal['catalog','product','category']='catalog'
    consent: Literal[True]


@router.get('/catalog')
def catalog(store=Depends(get_store)):
    return {'items':store.catalog(),'checked_at':int(time.time())}


@router.post('/events',status_code=202)
def event(payload: Event,store=Depends(get_store)):
    try:
        store.record_event(str(payload.event_id),payload.event_type,
                           offer_id=payload.offer_id,placement=payload.placement)
    except ValueError:
        raise HTTPException(422,'Invalid or unavailable offer event')
    return {'accepted':True}


@router.get('/admin',dependencies=[Depends(require_admin)])
def admin(store=Depends(get_store)):
    store.catalog()  # expire before reporting health
    with store.transaction() as c:
        offers=[dict(r) for r in c.execute('''SELECT o.id,o.product_id,p.title,o.status,o.reason,
            o.observed_at,o.expires_at FROM cp_offers o JOIN cp_products p ON p.id=o.product_id
            ORDER BY o.id DESC LIMIT 200''')]
        jobs=[dict(r) for r in c.execute('''SELECT id,job_type,status,attempt,available_at,error_code
            FROM cp_jobs ORDER BY id DESC LIMIT 100''')]
    return {'metrics':store.metrics(),'offers':offers,'jobs':jobs,'official_adapter_connected':False}


@router.post('/admin/import/preview',dependencies=[Depends(require_admin)])
def preview_import(payload: dict):
    try:
        return preview_official_records(payload.get('records'))
    except (ValueError,TypeError):
        raise HTTPException(422,'Invalid official offer preview batch')


@router.post('/admin/import',dependencies=[Depends(require_admin)],status_code=201)
def import_draft(payload: dict,store=Depends(get_store)):
    try:
        return store.ingest(payload)
    except (ValueError,TypeError):
        raise HTTPException(422,'Invalid official offer record; see COMPRAPULSE_DATA_MODEL.md')
