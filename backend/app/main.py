"""AION AI NEWS OS — production API and server-rendered SEO surfaces."""
import html
import json
import re
import time as _time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape as xml_escape

from starlette.requests import Request
from starlette.responses import JSONResponse

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from .agents.registry import process_queue_once, seed_agents
from .core import database as db
from .core.config import settings, site_url
from .core.security import require_admin
from .content_rules import quarantine_noncompliant_public_content
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
    # A fresh installation starts with image-gated editorial drafts.
    if not db.query_one("SELECT id FROM contents LIMIT 1"):
        from .bootstrap import seed_initial_content
        seed_initial_content()
    quarantine_noncompliant_public_content()
    # Process the editorial queue every hour.
    scheduler.add_job(process_queue_once, "interval", hours=1, id="content-pipeline")
    from .agents.orchestrator import run_cycle
    scheduler.add_job(lambda: run_cycle("scheduler"), "interval", hours=2, id="agent-orchestrator")
    # Run the first orchestrator cycle after startup.
    from datetime import datetime, timedelta
    scheduler.add_job(lambda: run_cycle("bootstrap"), "date",
                      run_date=datetime.now() + timedelta(seconds=45), id="first-cycle")
    scheduler.start()
    db.execute(
        "INSERT INTO logs (level, source, message) VALUES ('info','system','API started')"
    )
    yield
    scheduler.shutdown(wait=False)


SITE_URL = site_url()

app = FastAPI(
    title=settings.APP_NAME,
    description="API for the AION AI NEWS OS autonomous newsroom.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=False,
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
            return JSONResponse({"detail": "Too many attempts. Please wait one minute."}, status_code=429)
        _BUCKETS[key].append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
    )
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        "form-action 'self'; img-src 'self' https:; font-src 'self' https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "script-src 'self'; connect-src 'self' https://aion-news-api.onrender.com"
    )
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
            "Disallow: /login\nDisallow: /signup\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n"
            f"Sitemap: {SITE_URL}/news-sitemap.xml\n"
            f"Sitemap: {SITE_URL}/image-sitemap.xml\n")


@app.get("/sitemap.xml", tags=["seo"])
def sitemap():
    quarantine_noncompliant_public_content()
    base = SITE_URL
    static = ["", "/articles", "/categories", "/tags",
              "/about", "/privacy", "/terms", "/contact"]
    urls = [f"<url><loc>{xml_escape(base + p)}</loc></url>" for p in static]
    for c in db.query("SELECT slug, updated_at FROM contents WHERE status = 'published'"):
        urls.append(
            f"<url><loc>{xml_escape(base + '/article/' + c['slug'])}</loc>"
            f"<lastmod>{xml_escape(c['updated_at'][:10])}</lastmod></url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls) + "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/image-sitemap.xml", tags=["seo"])
def image_sitemap():
    """Image sitemap containing only publication-gated managed raster images."""
    quarantine_noncompliant_public_content()
    base = SITE_URL
    rows = db.query("""SELECT slug, title, image_url FROM contents
                       WHERE status='published' AND image_url LIKE 'http%'""")
    urls = "".join(
        f"<url><loc>{xml_escape(base + '/article/' + r['slug'])}</loc>"
        f"<image:image><image:loc>{xml_escape(r['image_url'])}</image:loc>"
        f"<image:title>{xml_escape(r['title'][:100])}</image:title>"
        f"</image:image></url>" for r in rows)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
           + urls + "</urlset>")
    return Response(content=xml, media_type="application/xml")


@app.get("/rss.xml", tags=["seo"])
def rss_feed():
    """Valid RSS 2.0 feed updated with each publication."""
    quarantine_noncompliant_public_content()
    base = SITE_URL
    rows = db.query("SELECT title, slug, excerpt, published_at, image_url FROM contents "
                    "WHERE status='published' ORDER BY published_at DESC LIMIT 30")
    def rss_date(value: str) -> str:
        try:
            parsed = datetime.fromisoformat((value or "").replace(" ", "T")).replace(tzinfo=timezone.utc)
            return format_datetime(parsed, usegmt=True)
        except Exception:
            return format_datetime(datetime.now(timezone.utc), usegmt=True)
    items = "".join(
        f"<item><title>{xml_escape(r['title'] or '')}</title>"
        f"<link>{xml_escape(base + '/article/' + r['slug'])}</link>"
        f"<guid isPermaLink=\"true\">{xml_escape(base + '/article/' + r['slug'])}</guid>"
        f"<description>{xml_escape(r['excerpt'] or '')}</description>"
        f"<enclosure url=\"{xml_escape(r['image_url'])}\" type=\"image/webp\" />"
        f"<pubDate>{rss_date(r['published_at'])}</pubDate></item>" for r in rows)
    xml = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
           '<title>AION AI NEWS OS</title>'
           f'<link>{base}</link>'
           '<description>AI news, guides and analysis from an autonomous newsroom.</description>'
           '<language>en-us</language>'
           f'{items}</channel></rss>')
    return Response(content=xml, media_type="application/rss+xml")


@app.get("/news-sitemap.xml", tags=["seo"])
def news_sitemap():
    """Google News sitemap: artigos publicados nas últimas 48 horas."""
    quarantine_noncompliant_public_content()
    base = SITE_URL
    rows = db.query(
        """SELECT slug, title, published_at FROM contents
           WHERE status='published' AND published_at > datetime('now','-2 days')
           ORDER BY published_at DESC LIMIT 100""")
    urls = "".join(
        f"<url><loc>{xml_escape(base + '/article/' + r['slug'])}</loc>"
        f"<news:news><news:publication><news:name>AION AI NEWS OS</news:name>"
        f"<news:language>en</news:language></news:publication>"
        f"<news:publication_date>{r['published_at'].replace(' ', 'T')}Z</news:publication_date>"
        f"<news:title>{xml_escape(r['title'][:110])}</news:title>"
        f"</news:news></url>" for r in rows)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
           + urls + "</urlset>")
    return Response(content=xml, media_type="application/xml")


def _rich_text(value: str) -> str:
    parts = re.split(r"(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))", value or "")
    rendered = []
    for part in parts:
        bold = re.fullmatch(r"\*\*([^*]+)\*\*", part)
        link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", part)
        if bold:
            rendered.append(f"<strong>{html.escape(bold.group(1))}</strong>")
        elif link:
            target = link.group(2)
            external = target.startswith(("https://", "http://"))
            internal = target.startswith("/") and not target.startswith("//")
            if external or internal:
                rel = ' rel="noopener nofollow"' if external else ""
                rendered.append(
                    f'<a href="{html.escape(target, quote=True)}"{rel}>'
                    f"{html.escape(link.group(1))}</a>"
                )
            else:
                rendered.append(html.escape(link.group(1)))
        else:
            rendered.append(html.escape(part))
    return "".join(rendered)


def _article_body(value: str) -> str:
    blocks = []
    for paragraph in re.split(r"\n\s*\n", value or ""):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph.startswith("## "):
            blocks.append(f"<h2>{_rich_text(paragraph[3:])}</h2>")
        elif paragraph.startswith("# "):
            blocks.append(f"<h2>{_rich_text(paragraph[2:])}</h2>")
        elif paragraph.startswith("- "):
            items = "".join(f"<li>{_rich_text(x[2:])}</li>" for x in paragraph.splitlines()
                            if x.startswith("- "))
            blocks.append(f"<ul>{items}</ul>")
        else:
            blocks.append(f"<p>{_rich_text(paragraph)}</p>")
    return "".join(blocks)


@app.get("/article/{slug}", response_class=HTMLResponse, include_in_schema=False)
def server_rendered_article(slug: str):
    """Indexable article HTML with unique Open Graph, Twitter and NewsArticle data."""
    quarantine_noncompliant_public_content()
    article = db.query_one(
        "SELECT * FROM contents WHERE slug=? AND status='published'", (slug,)
    )
    if not article:
        return HTMLResponse("<!doctype html><html lang='en-US'><title>Article not found — AION</title>"
                            "<h1>Article not found</h1><p><a href='/articles'>Browse articles</a></p></html>",
                            status_code=404)
    canonical = f"{SITE_URL}/article/{article['slug']}"
    title = (article["seo_title"] or article["title"])[:60]
    description = (article["seo_description"] or article["excerpt"])[:160]
    from .agents.imagegen import managed_image_path
    image = (article["hero_image_url"] if managed_image_path(article["hero_image_url"] or "")
             else article["image_url"])
    logo = f"{SITE_URL}/logo.png"
    jsonld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": article["title"][:110], "description": description,
        "datePublished": (article["published_at"] or "").replace(" ", "T") + "Z",
        "dateModified": (article["updated_at"] or "").replace(" ", "T") + "Z",
        "inLanguage": "en-US", "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "articleSection": article["category"] or "news",
        "keywords": [tag.strip() for tag in (article["tags"] or "").split(",") if tag.strip()],
        "image": {"@type": "ImageObject", "url": image, "width": 1200, "height": 630,
                  "caption": article["image_alt"] or article["title"],
                  "creditText": article["image_credit"] or "AION Editorial"},
        "author": {"@type": "Organization", "name": article["author"] or "AION Editorial",
                   "url": SITE_URL + "/about"},
        "publisher": {"@type": "NewsMediaOrganization", "name": "AION AI NEWS OS",
                      "url": SITE_URL + "/",
                      "logo": {"@type": "ImageObject", "url": logo, "width": 512, "height": 512}},
    }
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Articles", "item": SITE_URL + "/articles"},
            {"@type": "ListItem", "position": 3, "name": article["title"], "item": canonical},
        ],
    }
    page = f"""<!doctype html><html lang="en-US"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} — AION</title>
<meta name="description" content="{html.escape(description, quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{html.escape(canonical, quote=True)}"><link rel="alternate" hreflang="en-US" href="{html.escape(canonical, quote=True)}"><link rel="alternate" hreflang="x-default" href="{html.escape(canonical, quote=True)}"><link rel="icon" type="image/png" href="{SITE_URL}/logo.png">
<meta property="og:type" content="article"><meta property="og:site_name" content="AION AI NEWS OS">
<meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:url" content="{html.escape(canonical, quote=True)}"><meta property="og:image" content="{html.escape(image, quote=True)}"><meta property="og:image:alt" content="{html.escape(article['image_alt'] or article['title'], quote=True)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="en_US">
<meta property="article:published_time" content="{html.escape((article['published_at'] or '').replace(' ', 'T') + 'Z', quote=True)}"><meta property="article:modified_time" content="{html.escape((article['updated_at'] or '').replace(' ', 'T') + 'Z', quote=True)}">
<meta property="article:section" content="{html.escape(article['category'] or 'news', quote=True)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title, quote=True)}">
<meta name="twitter:description" content="{html.escape(description, quote=True)}"><meta name="twitter:image" content="{html.escape(image, quote=True)}"><meta name="twitter:image:alt" content="{html.escape(article['image_alt'] or article['title'], quote=True)}">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/')}</script>
<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False).replace('</', '<\\/')}</script>
<style>body{{margin:0;background:#08080f;color:#f6f3ff;font:17px/1.7 system-ui,sans-serif}}nav,main{{max-width:860px;margin:auto;padding:22px}}nav{{display:flex;justify-content:space-between}}a{{color:#a78bfa}}h1{{font-size:clamp(2.2rem,6vw,4rem);line-height:1.05}}h2{{margin-top:2rem;line-height:1.2}}img{{width:100%;height:auto;aspect-ratio:1200/630;object-fit:cover;border-radius:16px}}.meta{{color:#a8a4b8;font-size:.85rem}}.lead{{font-size:1.2rem;color:#c8c3d8}}</style></head>
<body><nav><a href="/">AION AI NEWS OS</a><a href="/articles">All articles</a></nav><main><article>
<p class="meta">{html.escape(article['category'] or 'news')} · {html.escape(article['author'] or 'AION Editorial')}</p>
<h1>{html.escape(article['title'])}</h1><img src="{html.escape(image, quote=True)}" alt="{html.escape(article['image_alt'] or article['title'], quote=True)}" width="1200" height="630">
<p class="lead">{html.escape(article['excerpt'] or '')}</p>{_article_body(article['body'])}</article></main></body></html>"""
    return HTMLResponse(page)


@app.get("/{asset}.png", include_in_schema=False)
def root_brand_asset(asset: str):
    if asset not in {"icon-192", "icon-512", "favicon", "og-cover"}:
        return Response(status_code=404)
    from .agents.imagegen import brand_asset_png
    return Response(brand_asset_png(asset), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400, stale-while-revalidate=604800"})


@app.post("/api/pipeline/run", tags=["content-queue"])
def run_pipeline_now(user: dict = Depends(require_admin)):
    """Run one content pipeline cycle on demand."""
    return process_queue_once()
