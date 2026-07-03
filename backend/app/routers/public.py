"""Rotas públicas do portal — artigos publicados, sem autenticação."""
from fastapi import APIRouter, HTTPException, status

from ..core import database as db

router = APIRouter(prefix="/api/public", tags=["public"])

_FIELDS = "id, title, slug, excerpt, seo_title, seo_description, published_at"


@router.get("/articles")
def list_articles(page: int = 1, per_page: int = 10):
    page = max(page, 1)
    per_page = min(max(per_page, 1), 50)
    total = db.query_one("SELECT COUNT(*) AS n FROM contents WHERE status = 'published'")["n"]
    items = db.query(
        f"""SELECT {_FIELDS} FROM contents WHERE status = 'published'
            ORDER BY published_at DESC LIMIT ? OFFSET ?""",
        (per_page, (page - 1) * per_page),
    )
    return {"items": items, "total": total, "page": page, "per_page": per_page}


@router.get("/articles/{slug}")
def get_article(slug: str):
    row = db.query_one(
        f"SELECT {_FIELDS}, body FROM contents WHERE slug = ? AND status = 'published'",
        (slug,),
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artigo não encontrado")
    return row
