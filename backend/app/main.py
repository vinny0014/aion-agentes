"""AION AGENTES — API principal (FastAPI)."""
from contextlib import asynccontextmanager

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
    health_router, logs_router, memory_router, queue_router, settings_router,
)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    seed_agents()
    # Scheduler de publicação diária: processa a fila de conteúdo a cada hora
    scheduler.add_job(process_queue_once, "interval", hours=1, id="content-pipeline")
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

for r in (auth_router, users_router, agents_router, content_router, tasks_router,
          logs_router, memory_router, settings_router, queue_router, health_router, public_router):
    app.include_router(r)


# ---------------- Endpoints públicos de SEO ----------------
@app.get("/robots.txt", response_class=PlainTextResponse, tags=["seo"])
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: https://aion-agentes.vercel.app/sitemap.xml\n"


@app.get("/sitemap.xml", tags=["seo"])
def sitemap():
    base = "https://aion-agentes.vercel.app"
    static = ["", "/sobre", "/login", "/cadastro"]
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
