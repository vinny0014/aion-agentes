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
from .routers.manus_bridge import router as manus_bridge_router
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
    app.state.scheduler = scheduler
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
    docs_url=None if settings.ENV.lower() == "production" else "/docs",
    redoc_url=None if settings.ENV.lower() == "production" else "/redoc",
    openapi_url=None if settings.ENV.lower() == "production" else "/openapi.json",
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
                "/api/public/contact": (5, 60), "/api/public/newsletter": (5, 60),
                "/internal/manus/webhook": (120, 60)}  # (req, janela s)


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
        "form-action 'self'; img-src 'self' https:; font-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self' https://aion-news-api.onrender.com"
    )
    if settings.ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    path = request.url.path
    if path == "/api/health" or (
        path.startswith("/api/")
        and (not path.startswith("/api/public/") or request.method != "GET")
    ):
        response.headers["Cache-Control"] = "no-store"
    elif request.method == "GET" and "cache-control" not in response.headers:
        if path.startswith("/api/public/"):
            response.headers["Cache-Control"] = "public, max-age=0, must-revalidate, s-maxage=60, stale-while-revalidate=600"
        elif path in {"/robots.txt", "/sitemap.xml", "/news-sitemap.xml", "/image-sitemap.xml", "/rss.xml"}:
            response.headers["Cache-Control"] = "public, max-age=300, s-maxage=600, stale-while-revalidate=86400"
        elif path.startswith("/article/"):
            response.headers["Cache-Control"] = "public, max-age=0, must-revalidate, s-maxage=60, stale-while-revalidate=600"
    return response


for r in (auth_router, users_router, agents_router, content_router, tasks_router,
          logs_router, memory_router, settings_router, queue_router, health_router, public_router, growth_router, orchestrator_router):
    app.include_router(r)

app.include_router(manus_bridge_router)


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
                rel = ' rel="noopener noreferrer"' if external else ""
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
    if managed_image_path(article["hero_image_url"] or ""):
        image = article["hero_image_url"]
        image_alt = article["hero_image_alt"] or article["image_alt"] or article["title"]
        image_credit = article["hero_image_credit"] or article["image_credit"] or "AION Editorial"
    else:
        image = article["image_url"]
        image_alt = article["image_alt"] or article["title"]
        image_credit = article["image_credit"] or "AION Editorial"
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
                  "caption": image_alt, "creditText": image_credit},
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
    source_html = ""
    if article["source_url"]:
        source_html = (
            f' · <a href="{html.escape(article["source_url"], quote=True)}" '
            'rel="noopener noreferrer">Primary source ↗</a>'
        )
    credit = image_credit
    caption = image_alt
    caption_html = (
        f'<figcaption>{html.escape(caption)}'
        f'{" · " + html.escape(credit) if credit else ""}</figcaption>'
    )
    published = html.escape((article["published_at"] or "")[:10])
    from .agents.discovery import reading_time_minutes
    reading_time = f' · {reading_time_minutes(article["body"] or "")} min read'
    plain_body = re.sub(r"(?m)^#+\s+.*$", " ", article["body"] or "")
    plain_body = re.sub(r"\*\*|\[([^]]+)\]\([^)]+\)", lambda match: match.group(1) or "", plain_body)
    takeaways = []
    for sentence in re.split(r"(?<=[.!?])\s+", f"{article['excerpt'] or ''} {plain_body}"):
        sentence = sentence.strip()
        if len(sentence) > 35 and sentence not in takeaways:
            takeaways.append(sentence)
        if len(takeaways) == 3:
            break
    takeaways_html = "".join(f"<li>{html.escape(item)}</li>" for item in takeaways)
    why_match = re.search(
        r"(?ims)^##?\s+Why it matters\s*$\s*(.*?)(?=^##?\s|\Z)", article["body"] or ""
    )
    why_text = (why_match.group(1).strip() if why_match else article["excerpt"] or "")
    source_entries = []
    if article["source_url"]:
        source_entries.append(("Primary source", article["source_url"]))
    for source_match in re.finditer(r"\[([^]]+)\]\((https?://[^)]+)\)", article["body"] or ""):
        entry = (source_match.group(1).strip(), source_match.group(2).strip())
        if entry[1] not in [existing[1] for existing in source_entries]:
            source_entries.append(entry)
        if len(source_entries) == 12:
            break
    source_items = "".join(
        f'<li><a class="source-link" href="{html.escape(url, quote=True)}" rel="noopener noreferrer">'
        f'{html.escape(label)} ↗</a></li>' for label, url in source_entries
    )
    sources_html = (
        '<section class="sources"><p class="eyebrow">Evidence</p><h2>Sources</h2>'
        f'<ul>{source_items}</ul></section>' if source_items else ""
    )
    tags_html = "".join(
        f'<a class="topic-link" data-topic="{html.escape(tag, quote=True)}" '
        f'href="/articles?tag={html.escape(tag, quote=True)}">{html.escape(tag)}</a>'
        for tag in [value.strip() for value in (article["tags"] or "").split(",") if value.strip()]
    )
    related = db.query(
        """SELECT id, title, slug, published_at, category FROM contents
           WHERE status='published' AND id<>?
           ORDER BY CASE WHEN category=? THEN 0 ELSE 1 END, published_at DESC LIMIT 3""",
        (article["id"], article["category"] or "news"),
    )
    related_cards = "".join(
        f'<a class="related-link" data-to-slug="{html.escape(item["slug"], quote=True)}" '
        f'href="/article/{html.escape(item["slug"], quote=True)}"><small>{html.escape(item["category"] or "News")}</small>'
        f'<strong>{html.escape(item["title"])}</strong><span>{html.escape((item["published_at"] or "")[:10])}</span></a>'
        for item in related
    )
    related_html = (
        f'<aside class="related"><p class="eyebrow">Keep reading</p><h2>Related stories</h2><div class="related-grid">{related_cards}</div></aside>'
        if related_cards else ""
    )
    next_html = ""
    if related:
        next_story = related[0]
        next_html = (
            '<section class="read-next"><p class="eyebrow">Continue the briefing</p><h2>Read next</h2>'
            f'<a class="next-story-link" data-to-slug="{html.escape(next_story["slug"], quote=True)}" '
            f'href="/article/{html.escape(next_story["slug"], quote=True)}">{html.escape(next_story["title"])} →</a></section>'
        )
    page = f"""<!doctype html><html lang="en-US"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} — AION</title>
<meta name="description" content="{html.escape(description, quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{html.escape(canonical, quote=True)}"><link rel="alternate" hreflang="en-US" href="{html.escape(canonical, quote=True)}"><link rel="alternate" hreflang="x-default" href="{html.escape(canonical, quote=True)}"><link rel="icon" type="image/png" href="{SITE_URL}/logo.png">
<meta property="og:type" content="article"><meta property="og:site_name" content="AION AI NEWS OS">
<meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:url" content="{html.escape(canonical, quote=True)}"><meta property="og:image" content="{html.escape(image, quote=True)}"><meta property="og:image:alt" content="{html.escape(image_alt, quote=True)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="en_US">
<meta property="article:published_time" content="{html.escape((article['published_at'] or '').replace(' ', 'T') + 'Z', quote=True)}"><meta property="article:modified_time" content="{html.escape((article['updated_at'] or '').replace(' ', 'T') + 'Z', quote=True)}">
<meta property="article:section" content="{html.escape(article['category'] or 'news', quote=True)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title, quote=True)}">
<meta name="twitter:description" content="{html.escape(description, quote=True)}"><meta name="twitter:image" content="{html.escape(image, quote=True)}"><meta name="twitter:image:alt" content="{html.escape(image_alt, quote=True)}">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/')}</script>
<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False).replace('</', '<\\/')}</script>
<style>
:root{{--bg:#08080f;--surface:#11101a;--ink:#f6f3ff;--muted:#aaa5b8;--line:#302d3b;--accent:#c084fc}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 ui-sans-serif,system-ui,-apple-system,sans-serif}}
a{{color:inherit;text-decoration:none}}a:hover{{color:var(--accent)}}.site-header{{position:sticky;top:0;z-index:10;border-bottom:1px solid var(--line);background:#08080ff2;backdrop-filter:blur(14px)}}
.header-inner,.article,.footer-inner{{width:min(100% - 40px,1120px);margin:auto}}.header-top{{display:flex;align-items:center;justify-content:space-between;padding:18px 0;border-bottom:1px solid var(--line)}}
.brand{{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.12em}}.mark{{display:grid;place-items:center;width:36px;height:36px;border:1px solid #c084fc99;font:700 20px Georgia,serif}}.brand small{{display:block;color:var(--muted);font-size:9px;letter-spacing:.3em}}
.nav-links{{display:flex;gap:24px;padding:10px 0;font-size:14px;color:var(--muted)}}.nav-links a:first-child{{color:var(--ink);font-weight:700}}.article{{max-width:920px;padding-top:62px;padding-bottom:72px}}
.eyebrow{{margin:0 0 14px;color:var(--accent);font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}}h1,h2{{font-family:Georgia,Cambria,'Times New Roman',serif}}h1{{max-width:900px;margin:0;font-size:clamp(2.6rem,7vw,5.1rem);line-height:1.02;letter-spacing:-.035em}}.lead{{max-width:780px;margin:22px 0;color:var(--muted);font-size:1.25rem;line-height:1.6}}
.byline{{display:flex;flex-wrap:wrap;gap:7px;margin:28px 0;border-block:1px solid var(--line);padding:14px 0;color:var(--muted);font-size:14px}}.byline strong{{color:var(--ink)}}.byline a{{color:var(--accent);font-weight:700}}
figure{{margin:32px 0 42px}}figure img{{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}}figcaption{{margin-top:8px;color:var(--muted);font-size:12px}}.body{{max-width:760px;margin:auto;font-size:1.12rem;line-height:1.9}}.body p{{margin:0 0 26px}}.body h2{{margin:50px 0 18px;border-top:1px solid var(--line);padding-top:28px;font-size:2rem;line-height:1.2}}.body a{{color:var(--accent);text-decoration:underline;text-decoration-color:#c084fc66;text-underline-offset:3px}}.body ul{{padding-left:24px}}
.takeaways,.why,.sources,.related,.read-next,.newsletter,.topics,.story-end{{max-width:760px;margin:42px auto 0}}.takeaways{{border-left:4px solid var(--accent);background:var(--surface);padding:24px}}.takeaways h2,.why h2,.sources h2,.related h2,.read-next h2{{margin:6px 0 14px;font-size:1.75rem;line-height:1.2}}.takeaways li{{margin:9px 0}}.why,.sources,.related,.read-next{{border-top:1px solid var(--line);padding-top:26px}}.why p:last-child{{color:var(--muted);font-size:1.08rem}}.sources a,.read-next a{{color:var(--accent);font-weight:800}}.topics{{display:flex;flex-wrap:wrap;gap:8px}}.topic-link{{border:1px solid var(--line);border-radius:999px;padding:4px 12px;color:var(--muted);font-size:12px}}.related-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.related-link{{display:flex;min-height:150px;flex-direction:column;justify-content:flex-end;border:1px solid var(--line);background:var(--surface);padding:16px}}.related-link small{{color:var(--accent);font-weight:800;text-transform:uppercase}}.related-link strong{{margin:6px 0;line-height:1.3}}.related-link span{{color:var(--muted);font-size:12px}}.read-next>a{{display:block;font:700 1.8rem/1.2 Georgia,serif}}.newsletter{{border-radius:8px;padding:28px;background:linear-gradient(145deg,#2e1065,#6d28d9 60%,#a21caf 120%)}}.newsletter h2{{margin:6px 0;font-size:2rem}}.newsletter p{{color:#ffffffb3}}.newsletter a{{display:inline-block;margin-top:8px;border-radius:5px;background:#fff;padding:9px 16px;color:#000;font-weight:800}}.story-end{{border-top:1px solid var(--line);padding-top:24px}}footer{{border-top:1px solid var(--line);padding:34px 0;color:var(--muted);font-size:13px}}.footer-inner{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:20px}}.footer-links{{display:flex;flex-wrap:wrap;gap:18px}}
@media(max-width:640px){{.header-inner,.article,.footer-inner{{width:min(100% - 30px,1120px)}}.tagline,.nav-links a:nth-child(n+4){{display:none}}.nav-links{{overflow:auto}}.article{{padding-top:38px}}h1{{font-size:2.7rem}}.lead{{font-size:1.1rem}}.related-grid{{grid-template-columns:1fr}}}}
</style></head>
<body><header class="site-header"><div class="header-inner"><div class="header-top"><a class="brand" href="/"><span class="mark">A</span><span>AION<small>AI NEWS</small></span></a><span class="tagline">Independent intelligence for the AI economy</span></div><nav class="nav-links" aria-label="Primary navigation"><a href="/">Top stories</a><a href="/articles">Latest</a><a href="/articles?category=analysis">Analysis</a><a href="/articles?category=guides">Guides</a><a href="/categories">All topics</a></nav></div></header>
<main><article class="article"><p class="eyebrow">{html.escape(article['category'] or 'AI intelligence')}</p><h1>{html.escape(article['title'])}</h1>
<p class="lead">{html.escape(article['excerpt'] or '')}</p><div class="byline"><strong>By {html.escape(article['author'] or 'AION Editorial')}</strong><span>·</span><time>{published}</time><span>{reading_time}</span>{source_html}</div>
<figure><img src="{html.escape(image, quote=True)}" alt="{html.escape(caption, quote=True)}" width="1200" height="630">{caption_html}</figure>
<aside class="takeaways"><p class="eyebrow">In brief</p><h2>Key takeaways</h2><ul>{takeaways_html}</ul></aside>
<section class="why"><p class="eyebrow">Context</p><h2>Why it matters</h2><p>{html.escape(why_text)}</p></section>
<div class="body">{_article_body(article['body'])}</div>{sources_html}<div class="topics">{tags_html}</div>{related_html}{next_html}
<section class="newsletter"><p class="eyebrow">The AION Brief</p><h2>One useful AI briefing. No hype.</h2><p>The developments that matter, what they mean and what to watch next.</p><a class="newsletter-link" href="/#newsletter">Join the briefing</a></section>
<div class="story-end"><a href="/articles">← All stories</a></div></article></main>
<footer><div class="footer-inner"><span>© {datetime.now(timezone.utc).year} AION AI News · Built by agents. Supervised by humans.</span><div class="footer-links"><a href="/about">About</a><a href="/editorial-policy">Editorial policy</a><a href="/corrections-policy">Corrections</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/contact">Contact</a></div></div></footer></body></html>"""
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
