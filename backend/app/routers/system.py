"""Routers de sistema — Logs, Memória, Configurações, Fila de Conteúdo, Health."""
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..core import database as db
from ..core.config import settings
from ..core.security import get_current_user, require_admin
from ..schemas import LogIn, MemoryIn, QueueIn, SettingIn

START_TIME = time.time()

# ====================== LOGS ======================
logs_router = APIRouter(prefix="/api/logs", tags=["logs"])


@logs_router.get("")
def list_logs(limit: int = 100, level: str | None = None, user: dict = Depends(require_admin)):
    limit = min(max(limit, 1), 500)
    if level:
        return db.query(
            "SELECT * FROM logs WHERE level = ? ORDER BY id DESC LIMIT ?", (level, limit)
        )
    return db.query("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))


@logs_router.post("", status_code=201)
def create_log(data: LogIn, user: dict = Depends(get_current_user)):
    lid = db.execute(
        "INSERT INTO logs (level, source, message, meta_json) VALUES (?,?,?,?)",
        (data.level, data.source, data.message, data.meta_json),
    )
    return db.query_one("SELECT * FROM logs WHERE id = ?", (lid,))


# ====================== MEMÓRIA ======================
memory_router = APIRouter(prefix="/api/memory", tags=["memory"])


@memory_router.get("")
def list_memory(scope: str | None = None, user: dict = Depends(get_current_user)):
    if scope:
        return db.query("SELECT * FROM memories WHERE scope = ? ORDER BY key", (scope,))
    return db.query("SELECT * FROM memories ORDER BY scope, key")


@memory_router.put("")
def upsert_memory(data: MemoryIn, user: dict = Depends(get_current_user)):
    db.execute(
        """INSERT INTO memories (scope, key, value) VALUES (?,?,?)
           ON CONFLICT(scope, key)
           DO UPDATE SET value = excluded.value, updated_at = datetime('now')""",
        (data.scope, data.key, data.value),
    )
    return db.query_one(
        "SELECT * FROM memories WHERE scope = ? AND key = ?", (data.scope, data.key)
    )


@memory_router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: int, user: dict = Depends(get_current_user)):
    if not db.query_one("SELECT id FROM memories WHERE id = ?", (memory_id,)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Memory entry not found")
    db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))


# ====================== CONFIGURAÇÕES ======================
settings_router = APIRouter(
    prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_admin)]
)

_PROTECTED_PREFIXES = ("secret", "token", "key", "password")


@settings_router.get("")
def list_settings():
    return db.query("SELECT * FROM app_settings ORDER BY key")


@settings_router.put("")
def upsert_setting(data: SettingIn):
    low = data.key.lower()
    if any(p in low for p in _PROTECTED_PREFIXES):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Secrets and API keys must stay in environment variables, never in the database",
        )
    db.execute(
        """INSERT INTO app_settings (key, value) VALUES (?,?)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')""",
        (data.key, data.value),
    )
    return db.query_one("SELECT * FROM app_settings WHERE key = ?", (data.key,))


@settings_router.delete("/{key}", status_code=204)
def delete_setting(key: str):
    db.execute("DELETE FROM app_settings WHERE key = ?", (key,))


# ====================== FILA DE CONTEÚDO ======================
queue_router = APIRouter(prefix="/api/content-queue", tags=["content-queue"])


@queue_router.get("")
def list_queue(user: dict = Depends(get_current_user)):
    return db.query("SELECT * FROM content_queue ORDER BY id DESC")


@queue_router.post("", status_code=201)
def enqueue(data: QueueIn, user: dict = Depends(get_current_user)):
    qid = db.execute(
        "INSERT INTO content_queue (topic, provider, template, scheduled_for) VALUES (?,?,?,?)",
        (data.topic, data.provider, data.template, data.scheduled_for),
    )
    return db.query_one("SELECT * FROM content_queue WHERE id = ?", (qid,))


@queue_router.delete("/{item_id}", status_code=204)
def dequeue(item_id: int, user: dict = Depends(get_current_user)):
    if not db.query_one("SELECT id FROM content_queue WHERE id = ?", (item_id,)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Queue item not found")
    db.execute("DELETE FROM content_queue WHERE id = ?", (item_id,))


# ====================== DISCOVERY GROWTH ======================
growth_router = APIRouter(prefix="/api/growth", tags=["discovery-growth"])


@growth_router.get("/report")
def get_growth_report(user: dict = Depends(require_admin)):
    from ..agents.discovery import growth_report
    return growth_report()


# ====================== ORQUESTRADOR MULTIAGENTE ======================
orchestrator_router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@orchestrator_router.post("/run")
def orchestrator_run(user: dict = Depends(require_admin)):
    """Executa um ciclo completo do pipeline multiagente (CEO Master)."""
    from ..agents.orchestrator import run_cycle
    return run_cycle("api")


@orchestrator_router.get("/runs")
def orchestrator_runs(limit: int = 50, agent: str | None = None,
                      user: dict = Depends(require_admin)):
    limit = min(max(limit, 1), 200)
    if agent:
        return db.query("SELECT * FROM agent_runs WHERE agent_slug = ? "
                        "ORDER BY id DESC LIMIT ?", (agent, limit))
    return db.query("SELECT * FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,))


@orchestrator_router.get("/health/google")
def google_health(user: dict = Depends(require_admin)):
    """Diagnóstico de prontidão Google: indexáveis, problemas e scores internos."""
    from ..agents.team import google_health_report
    return google_health_report()


@orchestrator_router.post("/cover")
def generate_cover(title: str, category: str = "news",
                   user: dict = Depends(require_admin)):
    """Generate and persist a real 1200x630 raster cover for Editorial Studio."""
    from ..agents.imagegen import materialize_remote_image, provider_photo_url
    candidate = provider_photo_url(title, category)
    prepared = materialize_remote_image(candidate[0], title) if candidate else None
    if not prepared:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "A real cover image could not be generated. Keep the article in draft and retry later.",
        )
    return {**prepared, "image_alt": f"Editorial image for {title[:90]}",
            "image_credit": candidate[1]}


@orchestrator_router.post("/upload-image")
async def upload_editorial_image(title: str, image: UploadFile = File(...),
                                 user: dict = Depends(require_admin)):
    """Validate an editor upload and persist it as a public WebP image."""
    if image.content_type == "image/svg+xml" or not (image.content_type or "").startswith("image/"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            "Only PNG, JPEG, WebP or GIF raster images are accepted")
    raw = await image.read(8_000_001)
    from ..agents.imagegen import materialize_uploaded_image
    prepared = materialize_uploaded_image(raw, title)
    if not prepared:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Image rejected: use a raster image up to 8 MB and at least 600x315 pixels",
        )
    return {**prepared, "image_alt": f"Editorial image for {title[:90]}",
            "image_credit": "Uploaded by AION Editorial"}


@orchestrator_router.get("/metrics")
def orchestrator_metrics(user: dict = Depends(require_admin)):
    from ..agents.core import agent_metrics, budget_remaining
    return {"por_agente": agent_metrics(),
            "orcamento_restante_usd": round(budget_remaining(), 4)}


# ====================== HEALTH CHECK ======================
health_router = APIRouter(tags=["health"])


@health_router.get("/api/health")
def health():
    db_ok = True
    try:
        db.query_one("SELECT 1 AS ok")
    except Exception:
        db_ok = False
    providers = {
        "openai": bool(settings.OPENAI_API_KEY),
        "anthropic": bool(settings.ANTHROPIC_API_KEY),
        "openrouter": bool(settings.OPENROUTER_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }
    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "database": "ok" if db_ok else "error",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "ai_providers_configured": providers,
    }
