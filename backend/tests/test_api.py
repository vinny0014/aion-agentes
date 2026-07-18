"""Production-readiness integration tests for AION AI NEWS OS."""
import io
import json
import os
import shutil
import sys
import asyncio
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
TEST_ROOT = Path("/tmp/aion-news-os-tests")
shutil.rmtree(TEST_ROOT, ignore_errors=True)
TEST_ROOT.mkdir(parents=True)

sys.path.insert(0, str(BACKEND))
os.environ.update({
    "DATABASE_URL": f"sqlite:///{TEST_ROOT / 'aion.db'}",
    "UPLOAD_DIR": str(TEST_ROOT / "uploads"),
    "PUBLIC_API_URL": "https://aion-news-api.onrender.com",
    "SITE_URL": "https://aion-news-os.vercel.app",
    "IMAGE_PROVIDER": "none",
    "SECRET_KEY": "test-secret-key-with-at-least-32-characters",
    "ADMIN_SETUP_TOKEN": "test-owner-setup-token",
    "CORS_ORIGINS": "https://aion-news-os.vercel.app",
    "ENV": "test",
})

import httpx  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from app.agents.imagegen import materialize_uploaded_image  # noqa: E402
from app.agents.registry import seed_agents  # noqa: E402
from app.core import database as db  # noqa: E402
from app.main import app  # noqa: E402

db.init_db()
seed_agents()

class ASGIClient:
    """Small synchronous facade over HTTPX's non-deprecated ASGI transport."""

    def request(self, method: str, path: str, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as session:
                return await session.request(method, path, **kwargs)
        return asyncio.run(send())

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def options(self, path: str, **kwargs):
        return self.request("OPTIONS", path, **kwargs)


client = ASGIClient()

ADMIN = {"name": "AION Owner", "email": "owner@example.com", "password": "StrongPassword123!"}
USER = {"name": "AION Reader", "email": "reader@example.com", "password": "StrongPassword123!"}
ADMIN_REGISTRATION = client.post("/api/auth/register", json={**ADMIN, "setup_token": "test-owner-setup-token"})
USER_REGISTRATION = client.post("/api/auth/register", json=USER)


def auth(account: dict) -> tuple[dict, str]:
    response = client.post("/api/auth/login", data={"username": account["email"], "password": account["password"]})
    assert response.status_code == 200, response.text
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}, tokens["refresh_token"]


ADMIN_HEADERS, _ = auth(ADMIN)
USER_HEADERS, _ = auth(USER)


def raster_bytes(width: int = 1200, height: int = 630, color: str = "#5634d1") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), color).save(output, "PNG")
    return output.getvalue()


TEST_IMAGE = materialize_uploaded_image(raster_bytes(), "integration test image")
assert TEST_IMAGE
TEST_IMAGE_URL = TEST_IMAGE["image_url"]


def article_payload(slug: str, **overrides) -> dict:
    payload = {
        "title": f"A practical guide to reliable AI systems {slug}",
        "slug": slug,
        "body": "## Reliable AI systems\n\nTeams can evaluate models, document sources, monitor outcomes and improve safeguards before every release. " * 8,
        "excerpt": "A practical English-language guide to building and operating reliable AI systems.",
        "status": "published",
        "category": "guides",
        "tags": "ai,reliability,engineering",
        "image_url": TEST_IMAGE_URL,
        "image_alt": "Engineers reviewing a reliable artificial intelligence system",
        "source_url": "https://example.com/research",
    }
    payload.update(overrides)
    return payload


def create_article(slug: str, **overrides) -> dict:
    response = client.post("/api/contents", headers=ADMIN_HEADERS, json=article_payload(slug, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


PRIMARY = create_article("reliable-ai-systems")


def test_health_and_security_headers():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "camera=()" in response.headers["permissions-policy"]


def test_production_rejects_weak_secrets_and_wildcard_cors():
    from app.core.config import Settings
    with pytest.raises(ValueError):
        Settings(_env_file=None, ENV="production", SECRET_KEY="weak",
                 ADMIN_SETUP_TOKEN="short", CORS_ORIGINS="*")


def test_owner_setup_is_explicit_and_single_use():
    assert ADMIN_REGISTRATION.status_code == 201
    assert ADMIN_REGISTRATION.json()["role"] == "admin"
    assert USER_REGISTRATION.status_code == 201
    assert USER_REGISTRATION.json()["role"] == "user"
    second = client.post("/api/auth/register", json={
        "name": "Second Owner", "email": "second-owner@example.com",
        "password": "StrongPassword123!", "setup_token": "test-owner-setup-token",
    })
    assert second.status_code == 409
    invalid = client.post("/api/auth/register", json={
        "name": "Invalid Owner", "email": "invalid-owner@example.com",
        "password": "StrongPassword123!", "setup_token": "wrong-token",
    })
    assert invalid.status_code == 403
    too_long = client.post("/api/auth/register", json={
        "name": "Long Password", "email": "long-password@example.com", "password": "é" * 40,
    })
    assert too_long.status_code == 422


def test_login_profile_and_refresh_rotation():
    headers, refresh = auth(ADMIN)
    assert client.get("/api/auth/me", headers=headers).json()["role"] == "admin"
    rotated = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": refresh}).status_code == 401
    assert client.post("/api/auth/login", data={"username": ADMIN["email"], "password": "wrong-password"}).status_code == 401


def test_admin_authorization_for_editorial_mutations():
    assert client.post("/api/contents", json=article_payload("anonymous-write")).status_code == 401
    assert client.post("/api/contents", headers=USER_HEADERS, json=article_payload("reader-write")).status_code == 403
    assert client.patch(f"/api/contents/{PRIMARY['id']}", headers=USER_HEADERS, json={"title": "Unauthorized"}).status_code == 403


def test_publication_requires_managed_raster_image():
    missing = client.post("/api/contents", headers=ADMIN_HEADERS,
                          json=article_payload("missing-image", image_url=""))
    assert missing.status_code == 422
    data_uri = client.post("/api/contents", headers=ADMIN_HEADERS,
                           json=article_payload("data-image", image_url="data:image/png;base64,AAAA"))
    assert data_uri.status_code == 422
    draft = client.post("/api/contents", headers=ADMIN_HEADERS,
                        json=article_payload("image-gated-draft", status="draft", image_url=""))
    assert draft.status_code == 201 and draft.json()["status"] == "draft"
    unsafe_source = client.post("/api/contents", headers=ADMIN_HEADERS,
                                json=article_payload("unsafe-source", source_url="javascript:alert(1)"))
    assert unsafe_source.status_code == 422


def test_publication_requires_english():
    response = client.post("/api/contents", headers=ADMIN_HEADERS, json=article_payload(
        "portuguese-blocked",
        title="Guia de inteligência artificial para empresas",
        excerpt="Um guia completo sobre inteligência artificial.",
        body="Este conteúdo explica como uma empresa pode usar inteligência artificial com segurança. " * 12,
    ))
    assert response.status_code == 422
    assert "English" in response.text


def test_valid_article_is_public_and_body_is_not_in_list():
    listing = client.get("/api/public/articles")
    assert listing.status_code == 200 and listing.json()["total"] >= 1
    item = next(item for item in listing.json()["items"] if item["slug"] == PRIMARY["slug"])
    assert "body" not in item
    detail = client.get(f"/api/public/articles/{PRIMARY['slug']}")
    assert detail.status_code == 200
    assert detail.json()["reading_time"] >= 1
    assert detail.json()["image_url"].startswith("https://aion-news-api.onrender.com/api/public/images/")


def test_search_categories_tags_and_related():
    create_article("ai-observability", category="analysis", tags="ai,observability")
    assert client.get("/api/public/articles?q=observability").json()["total"] >= 1
    assert any(row["category"] == "analysis" for row in client.get("/api/public/categories").json())
    assert any(row["tag"] == "ai" for row in client.get("/api/public/tags").json())
    related = client.get(f"/api/public/articles/{PRIMARY['slug']}/related")
    assert related.status_code == 200
    assert all(item["image_url"].startswith("https://") for item in related.json())


def test_newsletter_and_contact_flows():
    newsletter = client.post("/api/public/newsletter", json={"email": "subscriber@example.com"})
    assert newsletter.status_code == 201
    assert client.post("/api/public/newsletter", json={"email": "subscriber@example.com"}).status_code == 201
    contact = client.post("/api/public/contact", json={
        "name": "News Reader", "email": "reader-news@example.com", "message": "I have a story tip for the newsroom."
    })
    assert contact.status_code == 201
    logs = client.get("/api/logs", headers=ADMIN_HEADERS).json()
    assert any(log["source"] == "contato" for log in logs)


def test_image_upload_validation_and_delivery():
    assert client.post("/api/orchestrator/upload-image?title=Test", files={"image": ("x.png", raster_bytes(), "image/png")}).status_code == 401
    uploaded = client.post("/api/orchestrator/upload-image?title=Uploaded", headers=ADMIN_HEADERS,
                           files={"image": ("cover.png", raster_bytes(), "image/png")})
    assert uploaded.status_code == 200
    url = uploaded.json()["image_url"]
    path = url.split("/api/public", 1)[1]
    delivered = client.get(f"/api/public{path}")
    assert delivered.status_code == 200 and delivered.headers["content-type"] == "image/webp"
    assert "immutable" in delivered.headers["cache-control"]
    too_small = client.post("/api/orchestrator/upload-image?title=Small", headers=ADMIN_HEADERS,
                            files={"image": ("small.png", raster_bytes(200, 100), "image/png")})
    assert too_small.status_code == 422
    svg = client.post("/api/orchestrator/upload-image?title=SVG", headers=ADMIN_HEADERS,
                      files={"image": ("cover.svg", b"<svg/>", "image/svg+xml")})
    assert svg.status_code == 415


def test_cover_generation_fails_closed_without_provider():
    assert client.post("/api/orchestrator/cover?title=Test").status_code == 401
    response = client.post("/api/orchestrator/cover?title=Test", headers=ADMIN_HEADERS)
    assert response.status_code == 503
    assert "draft" in response.text


def test_brand_assets_are_real_pngs():
    for asset in ("favicon", "icon-192", "icon-512", "og-cover"):
        response = client.get(f"/{asset}.png")
        assert response.status_code == 200 and response.content.startswith(b"\x89PNG\r\n\x1a\n")

    for filename, dimensions in (("logo.png", (512, 512)), ("og-cover.png", (1200, 630))):
        with Image.open(ROOT / "frontend" / "public" / filename) as asset:
            assert asset.format == "PNG" and asset.size == dimensions


def test_robots_uses_only_official_domain_and_three_sitemaps():
    text = client.get("/robots.txt").text
    assert text.count("Sitemap: https://aion-news-os.vercel.app/") == 3
    assert "Disallow: /dashboard" in text
    assert "aion-agentes" + ".vercel.app" not in text


def test_sitemap_is_valid_and_contains_public_article():
    response = client.get("/sitemap.xml")
    root = ET.fromstring(response.content)
    assert root.tag.endswith("urlset")
    assert f"https://aion-news-os.vercel.app/article/{PRIMARY['slug']}" in response.text
    assert "/conte" + "udos" not in response.text and "/catego" + "rias" not in response.text


def test_news_sitemap_is_valid_english_and_recent():
    response = client.get("/news-sitemap.xml")
    root = ET.fromstring(response.content)
    assert root.tag.endswith("urlset")
    assert "<news:language>en</news:language>" in response.text
    assert "AION AI NEWS OS" in response.text


def test_image_sitemap_is_valid_and_escaped():
    response = client.get("/image-sitemap.xml")
    root = ET.fromstring(response.content)
    assert root.tag.endswith("urlset")
    assert TEST_IMAGE_URL in response.text
    assert "<image:image>" in response.text


def test_rss_is_valid_with_rfc822_dates_and_enclosures():
    response = client.get("/rss.xml")
    root = ET.fromstring(response.content)
    assert root.tag == "rss"
    items = root.findall("./channel/item")
    assert items
    assert parsedate_to_datetime(items[0].findtext("pubDate"))
    assert items[0].find("enclosure").attrib["url"].startswith("https://")
    assert root.findtext("./channel/language") == "en-us"


def test_server_rendered_article_has_complete_metadata():
    response = client.get(f"/article/{PRIMARY['slug']}")
    assert response.status_code == 200
    html = response.text
    assert '<html lang="en-US">' in html
    assert f'<link rel="canonical" href="https://aion-news-os.vercel.app/article/{PRIMARY["slug"]}">' in html
    assert '<meta property="og:type" content="article">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    assert '"@type": "NewsArticle"' in html and '"@type": "BreadcrumbList"' in html
    assert TEST_IMAGE_URL in html
    assert client.get("/article/not-published").status_code == 404
    from app.main import _rich_text
    assert 'href="/article/safe"' in _rich_text("[safe](/article/safe)")
    assert "javascript:" not in _rich_text("[unsafe](javascript:evil)")


def test_stale_external_hero_cannot_replace_managed_publication_image():
    db.execute("UPDATE contents SET hero_image_url='https://example.com/stale.jpg' WHERE id=?",
               (PRIMARY["id"],))
    hero = client.get("/api/public/hero")
    assert hero.status_code == 200
    if hero.json()["id"] == PRIMARY["id"]:
        assert hero.json()["image_url"] == TEST_IMAGE_URL
    rendered = client.get(f"/article/{PRIMARY['slug']}")
    assert TEST_IMAGE_URL in rendered.text
    assert "https://example.com/stale.jpg" not in rendered.text


def test_quarantine_moves_legacy_public_content_to_draft():
    legacy_id = db.execute(
        "INSERT INTO contents(title,slug,body,excerpt,status,image_url,published_at) VALUES(?,?,?,?,?,?,datetime('now'))",
        ("Legacy invalid story", "legacy-invalid-story", "English body", "Summary", "published", "data:image/svg+xml;base64,AA"),
    )
    from app.content_rules import quarantine_noncompliant_public_content
    result = quarantine_noncompliant_public_content()
    assert legacy_id in result["quarantined"]
    assert db.query_one("SELECT status FROM contents WHERE id=?", (legacy_id,))["status"] == "draft"


def test_public_read_gate_withdraws_article_when_managed_file_disappears():
    unique_image = materialize_uploaded_image(raster_bytes(color="#187a55"), "ephemeral image")
    assert unique_image
    article = create_article("withdrawn-missing-file", image_url=unique_image["image_url"])
    image_path = TEST_ROOT / "uploads" / unique_image["filename"]
    image_path.unlink()
    assert client.get(f"/api/public/articles/{article['slug']}").status_code == 404
    assert db.query_one("SELECT status FROM contents WHERE id=?", (article["id"],))["status"] == "draft"


def test_fact_check_and_publisher_respect_publication_gate():
    agent_id = db.query_one("SELECT id FROM agents WHERE slug='content'")["id"]
    content_id = db.execute(
        """INSERT INTO contents(title,slug,body,excerpt,status,agent_id,category,tags,image_url,image_alt)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        ("A complete analysis of model evaluation", "model-evaluation-analysis",
         "Teams evaluate artificial intelligence models with documented benchmarks, safety reviews and production monitoring. " * 70,
         "A complete guide to evaluating artificial intelligence models.", "draft", agent_id,
         "analysis", "ai,evaluation", TEST_IMAGE_URL, "A model evaluation dashboard"),
    )
    from app.agents.team import fact_check_agent, publisher_agent
    fact_check_agent({})
    published = publisher_agent({})
    assert published["auto_publicados"] >= 1
    assert db.query_one("SELECT status FROM contents WHERE id=?", (content_id,))["status"] == "published"

    invalid_id = db.execute(
        """INSERT INTO contents(title,slug,body,excerpt,status,agent_id,category,image_url,scheduled_at)
           VALUES(?,?,?,?,?,?,?,?,datetime('now','-1 hour'))""",
        ("Scheduled story without an image", "scheduled-without-image", "English editorial body " * 80,
         "A scheduled English story.", "draft", agent_id, "news", ""),
    )
    result = publisher_agent({})
    assert result["bloqueados"] >= 1
    assert db.query_one("SELECT status FROM contents WHERE id=?", (invalid_id,))["status"] == "draft"


def test_publisher_creates_new_discovery_content_as_draft_without_image():
    from app.agents.core import mem_set
    from app.agents.team import publisher_agent
    mem_set("agent:discovery", "manchetes_do_dia", [{
        "title": "Research lab announces a new evaluation framework",
        "link": "https://example.com/framework", "source": "https://example.com/feed",
        "image": "", "resumo": "The lab released a framework for independent model evaluation and documented testing. " * 3,
    }])
    result = publisher_agent({})
    assert result["radar"]
    row = db.query_one("SELECT status,image_url FROM contents WHERE id=?", (result["radar"]["id"],))
    assert row == {"status": "draft", "image_url": ""}


def test_pipeline_order_places_images_before_fact_check_and_publish():
    from app.agents.orchestrator import PIPELINE
    order = [step[0] for step in PIPELINE]
    assert order.index("image") < order.index("fact-check") < order.index("publisher")
    assert client.post("/api/pipeline/run").status_code == 401
    queued = client.post("/api/content-queue", headers=ADMIN_HEADERS, json={"topic": "Independent AI model evaluation"})
    assert queued.status_code == 201
    scheduled = client.post("/api/contents", headers=ADMIN_HEADERS, json=article_payload(
        "hourly-scheduled-publication", status="draft", scheduled_at="2000-01-01 00:00:00",
    ))
    assert scheduled.status_code == 201
    run = client.post("/api/pipeline/run", headers=ADMIN_HEADERS)
    assert run.status_code == 200 and run.json()["scheduled_published"] >= 1
    assert db.query_one("SELECT status FROM contents WHERE id=?", (scheduled.json()["id"],))["status"] == "published"


def test_agents_tasks_memory_logs_and_secret_settings_controls():
    agents = client.get("/api/agents", headers=ADMIN_HEADERS)
    assert agents.status_code == 200
    assert {"ceo-master", "content", "seo", "qa", "security"} <= {a["slug"] for a in agents.json()}
    task = client.post("/api/tasks", headers=USER_HEADERS, json={"title": "Review the homepage", "priority": 1})
    assert task.status_code == 201
    updated = client.patch(f"/api/tasks/{task.json()['id']}", headers=USER_HEADERS, json={"status": "done"})
    assert updated.json()["status"] == "done"
    memory = client.put("/api/memory", headers=USER_HEADERS, json={"scope": "test", "key": "language", "value": "en"})
    assert memory.status_code == 200
    assert client.put("/api/settings", headers=ADMIN_HEADERS, json={"key": "api_secret", "value": "nope"}).status_code == 400
    assert client.get("/api/logs", headers=USER_HEADERS).status_code == 403


def test_cors_allows_only_official_frontend():
    allowed = client.options("/api/public/articles", headers={
        "Origin": "https://aion-news-os.vercel.app", "Access-Control-Request-Method": "GET",
    })
    assert allowed.headers.get("access-control-allow-origin") == "https://aion-news-os.vercel.app"
    denied = client.options("/api/public/articles", headers={
        "Origin": "https://old.example.com", "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" not in denied.headers


def test_deployment_configs_align_official_services():
    render = (ROOT / "render.yaml").read_text()
    assert "name: aion-news-api" in render
    assert "https://aion-news-os.vercel.app" in render
    assert "https://aion-news-api.onrender.com" in render
    assert "autoDeployTrigger: checksPass" in render
    assert "value: 3.12.13" in render
    for path in (ROOT / "vercel.json", ROOT / "frontend" / "vercel.json"):
        config = json.loads(path.read_text())
        destinations = " ".join(rewrite["destination"] for rewrite in config["rewrites"])
        assert "https://aion-news-api.onrender.com/api/:path*" in destinations
        assert "https://aion-news-api.onrender.com/rss.xml" in destinations
        assert any(header["key"] == "Content-Security-Policy" for block in config["headers"] for header in block["headers"])


def test_no_static_feeds_or_old_public_routes_remain():
    public = ROOT / "frontend" / "public"
    for name in ("robots.txt", "sitemap.xml", "news-sitemap.xml", "image-sitemap.xml", "rss.xml"):
        assert not (public / name).exists()
    routes = (ROOT / "frontend" / "src" / "main.tsx").read_text()
    assert 'path="/conte' + 'udos"' not in routes
    assert 'path="/catego' + 'rias"' not in routes
    not_found = (public / "404.html").read_text()
    assert '<html lang="en-US">' in not_found and 'content="noindex,nofollow"' in not_found
    for config_path in (ROOT / "vercel.json", ROOT / "frontend" / "vercel.json"):
        config = json.loads(config_path.read_text())
        assert not any(rewrite["source"] == "/:path*" for rewrite in config["rewrites"])


def test_no_deprecated_domains_or_committed_secrets():
    forbidden = ("wordbet" + ".com.br", "aion-agentes" + ".vercel.app",
                 "aion-agentes-api" + ".onrender.com")
    source_files = [
        ROOT / "backend" / "app" / "main.py", ROOT / "backend" / "app" / "core" / "config.py",
        ROOT / "render.yaml", ROOT / "vercel.json", ROOT / "frontend" / "vercel.json",
        ROOT / "frontend" / "index.html", ROOT / "frontend" / "src" / "lib" / "site.ts",
    ]
    text = "\n".join(path.read_text() for path in source_files)
    assert not any(domain in text for domain in forbidden)
    assert not (ROOT / "backend" / ".env").exists()
    assert "CHANGE_ME_IN_ENV" not in (ROOT / "render.yaml").read_text()


def test_ci_runs_backend_and_frontend_validation():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "python -m pytest" in workflow
    assert "npm ci" in workflow and "npm run build" in workflow
    assert "playwright install --with-deps chromium" in workflow and "npm run test:e2e" in workflow
