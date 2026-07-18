"""Rotas públicas do portal — sem autenticação, otimizadas para SEO e tráfego."""
import json
import re
from collections import Counter

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response

from ..core import database as db
from ..agents.discovery import reading_time_minutes, related_articles
from ..content_rules import quarantine_noncompliant_public_content
from ..schemas import ContactIn, EmailIn

router = APIRouter(prefix="/api/public", tags=["public"])

_FIELDS = "id, title, slug, excerpt, seo_title, seo_description, category, tags, image_url, image_alt, image_credit, image_width, image_height, hero_image_url, hero_image_alt, hero_image_credit, hero_image_width, hero_image_height, hero_image_source, source_url, author, featured, pinned, breaking_flag, editors_pick, published_at, updated_at"


@router.get("/articles")
def list_articles(page: int = 1, per_page: int = 10, category: str = "",
                  tag: str = "", q: str = ""):
    quarantine_noncompliant_public_content()
    page = max(page, 1)
    per_page = min(max(per_page, 1), 50)
    where, params = ["status = 'published'"], []
    if category:
        where.append("category = ?")
        params.append(category.strip().lower())
    if tag:
        where.append("(',' || tags || ',') LIKE ?")
        params.append(f"%,{tag.strip().lower()},%")
    if q:
        where.append("(title LIKE ? OR excerpt LIKE ? OR body LIKE ?)")
        like = f"%{q.strip()}%"
        params += [like, like, like]
    w = " AND ".join(where)
    total = db.query_one(f"SELECT COUNT(*) AS n FROM contents WHERE {w}", tuple(params))["n"]
    items = db.query(
        f"SELECT {_FIELDS} FROM contents WHERE {w} ORDER BY pinned DESC, published_at DESC LIMIT ? OFFSET ?",
        (*params, per_page, (page - 1) * per_page),
    )
    return {"items": items, "total": total, "page": page, "per_page": per_page,
            "category": category, "tag": tag, "q": q}


@router.get("/articles/{slug}")
def get_article(slug: str):
    quarantine_noncompliant_public_content()
    row = db.query_one(
        f"SELECT {_FIELDS}, body FROM contents WHERE slug = ? AND status = 'published'",
        (slug,),
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
    row["reading_time"] = reading_time_minutes(row["body"])
    return row


@router.get("/articles/{slug}/related")
def get_related(slug: str, limit: int = 3):
    quarantine_noncompliant_public_content()
    return related_articles(slug, min(max(limit, 1), 6))


@router.get("/hero")
def get_hero():
    """Matéria do hero: Breaking News se houver, senão a mais recente."""
    quarantine_noncompliant_public_content()
    from ..agents.core import mem_get
    from ..agents.team import hero_ranking
    breaking = mem_get("agent:breaking-news", "hero") or {}
    rank = hero_ranking()
    if rank:
        row = db.query_one(
            f"SELECT {_FIELDS} FROM contents WHERE slug=? AND status='published'",
            (rank["slug"],))
        if row:
            row["breaking"] = rank["slug"] == breaking.get("slug")
            row["hero_score"] = rank["score"]
            from ..agents.imagegen import managed_image_path
            if managed_image_path(row.get("hero_image_url") or ""):
                row["image_url"] = row["hero_image_url"]
                row["image_alt"] = row["hero_image_alt"] or row["image_alt"]
                row["image_credit"] = row["hero_image_credit"] or row["image_credit"]
            return row
    row = db.query_one(
        f"SELECT {_FIELDS} FROM contents WHERE status='published' "
        "ORDER BY published_at DESC LIMIT 1")
    if not row:
        # An empty newsroom is a valid bootstrap state, not a broken resource.
        # Returning JSON null avoids a noisy browser 404 while the publication
        # gate and scheduler prepare the first eligible story.
        return None
    row["breaking"] = False
    return row


@router.get("/categories")
def list_categories():
    quarantine_noncompliant_public_content()
    return db.query(
        """SELECT category, COUNT(*) AS total FROM contents
           WHERE status = 'published' AND category != ''
           GROUP BY category ORDER BY total DESC, category"""
    )


@router.get("/tags")
def list_tags():
    quarantine_noncompliant_public_content()
    rows = db.query("SELECT tags FROM contents WHERE status = 'published' AND tags != ''")
    counter = Counter()
    for r in rows:
        counter.update(t for t in r["tags"].split(",") if t)
    return [{"tag": t, "total": n} for t, n in counter.most_common()]


@router.post("/contact", status_code=201)
def contact(data: ContactIn):
    """Public contact form; messages are recorded in the admin logs."""
    db.execute(
        "INSERT INTO logs (level, source, message, meta_json) VALUES ('info','contato',?,?)",
        (f"Message from {data.name}: {data.message[:200]}",
         json.dumps({"name": data.name, "email": data.email, "message": data.message})),
    )
    return {"ok": True, "detail": "Message received. Thank you for contacting us!"}


@router.post("/newsletter", status_code=201)
def newsletter_subscribe(data: EmailIn):
    """Inscrição na newsletter — requer apenas o e-mail."""
    if not db.query_one("SELECT id FROM subscribers WHERE email = ?", (data.email,)):
        db.execute("INSERT INTO subscribers (email, segment) VALUES (?, 'geral')", (data.email,))
    return {"ok": True, "detail": "Subscription confirmed!"}


@router.get("/images/{filename}", include_in_schema=False)
def public_image(filename: str):
    """Serve only validated raster files stored by the image pipeline."""
    if not re.fullmatch(r"[a-z0-9-]+\.(?:webp|png|jpe?g)", filename):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    from ..agents.imagegen import _upload_dir
    path = _upload_dir() / filename
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=31536000, immutable"})


@router.get("/assets/{asset}.png", include_in_schema=False)
def brand_asset(asset: str):
    if asset not in {"icon-192", "icon-512", "favicon", "og-cover"}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    from ..agents.imagegen import brand_asset_png
    return Response(
        brand_asset_png(asset),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400, stale-while-revalidate=604800"},
    )
