"""AION AGENTES — API principal (FastAPI)."""
import time as _time
from collections import defaultdict
from contextlib import asynccontextmanager

from starlette.requests import Request
from starlette.responses import JSONResponse

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response

from .agents.registry import process_queue_once, seed_agents
from .core import database as db
from .core.config import settings
from .routers.auth import router as auth_router
from .routers.public import router as public_router
from .routers.crud import agents_router, content_router, tasks_router, users_router
from .routers.system import (
    growth_router, orchestrator_router, health_router, logs_router, memory_router, queue_router, settings_router,
)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    seed_agents()
    # Bootstrap de produção: se não há nenhum conteúdo, publica os guias iniciais
    if not db.query_one("SELECT id FROM contents LIMIT 1"):
        from .bootstrap import seed_initial_content
        seed_initial_content()
    # Scheduler de publicação diária: processa a fila de conteúdo a cada hora
    scheduler.add_job(process_queue_once, "interval", hours=1, id="content-pipeline")
    from .agents.orchestrator import run_cycle
    scheduler.add_job(lambda: run_cycle("scheduler"), "interval", hours=6, id="agent-orchestrator")
    # Primeiro ciclo logo após o boot (popula o portal sem intervenção manual)
    from datetime import datetime, timedelta
    scheduler.add_job(lambda: run_cycle("bootstrap"), "date",
                      run_date=datetime.now() + timedelta(seconds=45), id="first-cycle")
    scheduler.start()
    db.execute(
        "INSERT INTO logs (level, source, message) VALUES ('info','system','API iniciada')"
    )
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    description="API do portal AION AGENTES — conteúdo diário e agentes inteligentes.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Middlewares de segurança ----------------
_BUCKETS: dict[str, list[float]] = defaultdict(list)
_RATE_LIMITS = {"/api/auth/login": (10, 60), "/api/auth/register": (5, 60),
                "/api/public/contact": (5, 60), "/api/public/newsletter": (5, 60)}  # (req, janela s)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    limit = _RATE_LIMITS.get(request.url.path)
    if limit and request.method == "POST" and settings.ENV != "test":
        max_req, window = limit
        ip = request.client.host if request.client else "?"
        key = f"{ip}:{request.url.path}"
        now = _time.time()
        _BUCKETS[key] = [t for t in _BUCKETS[key] if now - t < window]
        if len(_BUCKETS[key]) >= max_req:
            return JSONResponse({"detail": "Muitas tentativas. Aguarde um minuto."}, status_code=429)
        _BUCKETS[key].append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


for r in (auth_router, users_router, agents_router, content_router, tasks_router,
          logs_router, memory_router, settings_router, queue_router, health_router, public_router, growth_router, orchestrator_router):
    app.include_router(r)


# ---------------- Endpoints públicos de SEO ----------------
@app.get("/robots.txt", response_class=PlainTextResponse, tags=["seo"])
def robots():
    return ("User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin\nDisallow: /dashboard\n"
            "Sitemap: https://aion-agentes.vercel.app/sitemap.xml\n")


@app.get("/sitemap.xml", tags=["seo"])
def sitemap():
    base = "https://aion-agentes.vercel.app"
    static = ["", "/sobre", "/conteudos", "/categorias", "/tags",
              "/privacidade", "/termos", "/contato"]
    urls = [f"<url><loc>{base}{p}</loc></url>" for p in static]
    for c in db.query("SELECT slug, updated_at FROM contents WHERE status = 'published'"):
        urls.append(
            f"<url><loc>{base}/conteudo/{c['slug']}</loc>"
            f"<lastmod>{c['updated_at'][:10]}</lastmod></url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls) + "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@app.post("/api/pipeline/run", tags=["content-queue"])
def run_pipeline_now():
    """Dispara manualmente um ciclo do pipeline de conteúdo."""
    return process_queue_once()
