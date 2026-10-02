"""Opt-in commerce API, reusing the existing admin authorization."""
import time
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from ..core import database as db
from ..core.config import settings
from ..core.security import require_admin
from .adapters import AdapterUnavailable, ShopeeOfficialCsvAdapter
from .importers import (
    issue_preview_receipt,
    preview_official_records,
    verify_preview_receipt,
)
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


class PreviewImport(BaseModel):
    model_config=ConfigDict(extra='forbid')
    records: list[dict]


class DraftImport(BaseModel):
    model_config=ConfigDict(extra='forbid')
    record: dict
    preview_receipt: str=Field(min_length=1,max_length=256)


class CsvPilotSelection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    row_index: int=Field(ge=0,le=ShopeeOfficialCsvAdapter.max_pilot_row_index)


class CsvPilotImport(CsvPilotSelection):
    preview_receipt: str=Field(min_length=1,max_length=256)


def csv_adapter_configured() -> bool:
    path=settings.COMPRAPULSE_SHOPEE_CSV_PATH
    return bool(path and settings.COMPRAPULSE_SHOPEE_CSV_OBSERVED_AT > 0
                and Path(path).is_file())


def csv_adapter() -> ShopeeOfficialCsvAdapter:
    if not csv_adapter_configured():
        raise HTTPException(503,'Official Shopee export is not configured')
    return ShopeeOfficialCsvAdapter(
        settings.COMPRAPULSE_SHOPEE_CSV_PATH,
        observed_at=settings.COMPRAPULSE_SHOPEE_CSV_OBSERVED_AT,
    )


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
    return {'metrics':store.metrics(),'offers':offers,'jobs':jobs,
            'official_adapter_connected':csv_adapter_configured()}


@router.post('/admin/import/preview',dependencies=[Depends(require_admin)])
def preview_import(payload: PreviewImport):
    try:
        result=preview_official_records(payload.records)
        result['preview_receipts']=[
            {'index':index,'receipt':issue_preview_receipt(
                payload.records[index],secret=settings.SECRET_KEY)}
            for index in result['accepted_indexes']
        ]
        return result
    except (ValueError,TypeError):
        raise HTTPException(422,'Invalid official offer preview batch')


@router.post('/admin/import',dependencies=[Depends(require_admin)],status_code=201)
def import_draft(payload: DraftImport,store=Depends(get_store)):
    try:
        verify_preview_receipt(
            payload.record,payload.preview_receipt,secret=settings.SECRET_KEY)
        return store.ingest(payload.record)
    except (ValueError,TypeError):
        raise HTTPException(422,'Invalid or expired official offer preview')


@router.post('/admin/import/preview-csv',dependencies=[Depends(require_admin)])
def preview_csv_pilot(payload: CsvPilotSelection):
    try:
        record=dict(csv_adapter().fetch_offer_at(payload.row_index).records[0])
        result=preview_official_records([record])
        if result['accepted_count'] != 1:
            raise ValueError('invalid_export_record')
        return {
            'row_index':payload.row_index,
            'candidate':{key:record[key] for key in (
                'product_id','title','category','price_cents','observed_at','expires_at')},
            'image_present':True,
            'preview_receipt':issue_preview_receipt(record,secret=settings.SECRET_KEY),
            'persisted':False,
            'published':False,
        }
    except HTTPException:
        raise
    except (AdapterUnavailable,ValueError,TypeError,KeyError):
        raise HTTPException(422,'Invalid or stale official Shopee export selection')


@router.post('/admin/import/csv',dependencies=[Depends(require_admin)],status_code=201)
def import_csv_pilot(payload: CsvPilotImport,store=Depends(get_store)):
    try:
        record=dict(csv_adapter().fetch_offer_at(payload.row_index).records[0])
        verify_preview_receipt(
            record,payload.preview_receipt,secret=settings.SECRET_KEY)
        return store.ingest(record)
    except HTTPException:
        raise
    except (AdapterUnavailable,ValueError,TypeError,KeyError):
        raise HTTPException(422,'Invalid or expired official Shopee CSV preview')
