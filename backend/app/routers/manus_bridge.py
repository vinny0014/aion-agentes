"""Authenticated, auditable coordination bridge for Manus tasks.

The webhook endpoint has a deliberately inert bootstrap mode so Manus can
validate reachability before the RSA public key is configured. Once the key is
present, every event must pass signature, freshness, size and idempotency
checks before it is stored. Outbound task operations require a separate bridge
token and never expose provider credentials.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import time
from typing import Any

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from ..core import database as db
from ..core.config import settings


router = APIRouter(prefix="/internal/manus", tags=["internal-manus"])

MAX_WEBHOOK_BYTES = 64 * 1024
MAX_MESSAGE_CHARS = 50_000
ALLOWED_EVENTS = {"task_created", "task_stopped"}
EVENT_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")
AUTOMATION_GUARDRAILS = """AUTOMATED AION NEWS OPERATION.
Do not make payments, purchases, plan changes, DNS changes, destructive deletions,
or disclose secrets. Stop only for payment, CAPTCHA, 2FA, mandatory human approval,
or an irreversible decision. Preserve AION Crypto, main, and unrelated projects.

TASK:
"""


class ManusTaskIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=50_000)
    title: str = Field(default="AION News operation", min_length=1, max_length=200)


class ManusMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=50_000)


def _configured_public_key() -> str:
    return settings.MANUS_WEBHOOK_PUBLIC_KEY.strip().replace("\\n", "\n")


def _require_bridge_token(
    x_aion_bridge_token: str | None = Header(default=None),
) -> None:
    configured = settings.AION_BRIDGE_TOKEN
    if len(configured) < 32:
        raise HTTPException(status_code=503, detail="Bridge control is not configured")
    if not x_aion_bridge_token or not hmac.compare_digest(
        x_aion_bridge_token, configured
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _read_limited_body(request: Request) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_WEBHOOK_BYTES:
                raise HTTPException(status_code=413, detail="Payload too large")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Content-Length") from exc

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_WEBHOOK_BYTES:
            raise HTTPException(status_code=413, detail="Payload too large")
    return bytes(body)


def _signed_url(request: Request) -> str:
    """Return the exact public URL registered with Manus.

    Using PUBLIC_API_URL avoids trusting spoofable Host/Forwarded headers and
    avoids Render's internal proxy scheme leaking into signature validation.
    """
    url = f"{settings.PUBLIC_API_URL.rstrip('/')}{request.url.path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    return url


def _verify_signature(request: Request, body: bytes, public_key_pem: str) -> None:
    signature_b64 = request.headers.get("x-webhook-signature", "")
    timestamp = request.headers.get("x-webhook-timestamp", "")
    if not signature_b64 or not timestamp:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc
    if abs(int(time.time()) - timestamp_value) > 300:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body_hash = hashlib.sha256(body).hexdigest()
    signed_content = f"{timestamp}.{_signed_url(request)}.{body_hash}".encode()
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        public_key.verify(
            signature,
            signed_content,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except (InvalidSignature, ValueError, TypeError, binascii.Error) as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc


def _normalize_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_id = str(payload.get("event_id", ""))
    event_type = str(payload.get("event_type", ""))
    detail = payload.get("task_detail")
    if not EVENT_ID_RE.fullmatch(event_id) or event_type not in ALLOWED_EVENTS:
        raise HTTPException(status_code=422, detail="Unsupported webhook event")
    if not isinstance(detail, dict):
        raise HTTPException(status_code=422, detail="Invalid task detail")

    task_id = str(detail.get("task_id", ""))[:256]
    if not task_id:
        raise HTTPException(status_code=422, detail="Missing task ID")
    stop_reason = str(detail.get("stop_reason", ""))[:32]
    if event_type == "task_stopped" and stop_reason not in {"finish", "ask"}:
        raise HTTPException(status_code=422, detail="Invalid stop reason")

    attachments = []
    for item in detail.get("attachments") or []:
        if isinstance(item, dict):
            try:
                size_bytes = max(0, int(item.get("size_bytes", 0) or 0))
            except (TypeError, ValueError):
                size_bytes = 0
            attachments.append({
                "file_name": str(item.get("file_name", ""))[:255],
                "size_bytes": size_bytes,
            })

    # Signed download URLs and arbitrary structured output are intentionally
    # omitted from persistent storage. They can contain time-limited secrets or
    # unbounded provider data.
    audit_payload = {
        "event_id": event_id,
        "event_type": event_type,
        "task_detail": {
            "task_id": task_id,
            "task_title": str(detail.get("task_title", ""))[:500],
            "task_url": str(detail.get("task_url", ""))[:1000],
            "stop_reason": stop_reason,
            "attachments": attachments[:20],
        },
    }
    return {
        "event_id": event_id,
        "event_type": event_type,
        "task_id": task_id,
        "task_title": str(detail.get("task_title", ""))[:500],
        "stop_reason": stop_reason,
        "message": str(detail.get("message", ""))[:MAX_MESSAGE_CHARS],
        "payload_json": json.dumps(audit_payload, ensure_ascii=False),
    }


@router.get("/status")
def bridge_status():
    """Expose capability flags only; never return secrets or task contents."""
    return {
        "webhook_verification": bool(_configured_public_key()),
        "outbound_api": bool(settings.MANUS_API_KEY),
        "control_auth": len(settings.AION_BRIDGE_TOKEN) >= 32,
    }


@router.post("/webhook", status_code=200)
async def manus_webhook(request: Request):
    body = await _read_limited_body(request)
    public_key_pem = _configured_public_key()
    if not public_key_pem:
        # Registration bootstrap only: prove reachability, with a bounded body,
        # but do not parse, process or persist anything unauthenticated.
        return {"status": "webhook_registration_pending"}

    _verify_signature(request, body, public_key_pem)
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Invalid webhook payload")
    event = _normalize_event(payload)

    try:
        db.execute(
            """INSERT INTO manus_bridge_events
               (event_id, event_type, task_id, task_title, stop_reason, message, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                event["event_id"], event["event_type"], event["task_id"],
                event["task_title"], event["stop_reason"], event["message"],
                event["payload_json"],
            ),
        )
        db.execute(
            "INSERT INTO logs (level, source, message, meta_json) VALUES (?, ?, ?, ?)",
            (
                "info", "manus-bridge", f"Received {event['event_type']}",
                json.dumps({"event_id": event["event_id"], "task_id": event["task_id"]}),
            ),
        )
    except Exception as exc:
        # Duplicate event IDs are successful idempotent retries. Do not leak
        # database details for any other failure.
        existing = db.query_one(
            "SELECT id FROM manus_bridge_events WHERE event_id = ?",
            (event["event_id"],),
        )
        if not existing:
            raise HTTPException(status_code=500, detail="Event persistence failed") from exc
    return {"status": "accepted", "event_id": event["event_id"]}


@router.get("/events", dependencies=[Depends(_require_bridge_token)])
def list_bridge_events(status: str = "received", limit: int = 50):
    if status not in {"received", "processed", "failed", "all"}:
        raise HTTPException(status_code=422, detail="Invalid status")
    limit = max(1, min(limit, 100))
    if status == "all":
        return db.query(
            """SELECT id, event_id, event_type, task_id, task_title, status,
                      stop_reason, message, received_at, processed_at
               FROM manus_bridge_events ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
    return db.query(
        """SELECT id, event_id, event_type, task_id, task_title, status,
                  stop_reason, message, received_at, processed_at
           FROM manus_bridge_events WHERE status = ? ORDER BY id LIMIT ?""",
        (status, limit),
    )


@router.post("/events/{event_id}/ack", dependencies=[Depends(_require_bridge_token)])
def acknowledge_event(event_id: str):
    if not EVENT_ID_RE.fullmatch(event_id):
        raise HTTPException(status_code=422, detail="Invalid event ID")
    existing = db.query_one(
        "SELECT id FROM manus_bridge_events WHERE event_id = ?", (event_id,)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    db.execute(
        """UPDATE manus_bridge_events SET status='processed',
           processed_at=datetime('now') WHERE event_id = ?""",
        (event_id,),
    )
    return {"status": "processed", "event_id": event_id}


async def _manus_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not settings.MANUS_API_KEY:
        raise HTTPException(status_code=503, detail="Manus outbound API is not configured")
    url = f"{settings.MANUS_API_BASE_URL.rstrip('/')}/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            response = await client.post(
                url,
                headers={
                    "x-manus-api-key": settings.MANUS_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Manus API request failed") from exc
    if not isinstance(data, dict) or data.get("ok") is not True:
        raise HTTPException(status_code=502, detail="Manus API rejected the request")
    return data


@router.post("/tasks", dependencies=[Depends(_require_bridge_token)])
async def create_manus_task(payload: ManusTaskIn):
    body: dict[str, Any] = {
        "message": {"content": [{
            "type": "text", "text": AUTOMATION_GUARDRAILS + payload.prompt,
        }]},
        "title": payload.title,
        "interactive_mode": False,
        "share_visibility": "private",
    }
    if settings.MANUS_PROJECT_ID:
        body["project_id"] = settings.MANUS_PROJECT_ID
    data = await _manus_post("task.create", body)
    db.execute(
        "INSERT INTO logs (level, source, message, meta_json) VALUES (?, ?, ?, ?)",
        (
            "info", "manus-bridge", "Created Manus task",
            json.dumps({"task_id": data.get("task_id"), "title": payload.title}),
        ),
    )
    return {
        "task_id": data.get("task_id"),
        "task_title": data.get("task_title"),
        "task_url": data.get("task_url"),
    }


@router.post("/tasks/{task_id}/messages", dependencies=[Depends(_require_bridge_token)])
async def send_manus_message(task_id: str, payload: ManusMessageIn):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", task_id):
        raise HTTPException(status_code=422, detail="Invalid task ID")
    data = await _manus_post(
        "task.sendMessage",
        {
            "task_id": task_id,
            "message": {"content": [{
                "type": "text", "text": AUTOMATION_GUARDRAILS + payload.message,
            }]},
        },
    )
    return {"task_id": data.get("task_id"), "status": "sent"}
