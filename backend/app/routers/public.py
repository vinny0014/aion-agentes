"""Rotas públicas do portal — sem autenticação, otimizadas para SEO e tráfego."""
import json
from collections import Counter

from fastapi import APIRouter, HTTPException, status

from ..core import database as db
from ..agents.discovery import reading_time_minutes, related_articles
from ..schemas import ContactIn

router = APIRouter(prefix="/api/public", tags=["public"])

_FIELDS = "id, title, slug, excerpt, seo_title, seo_description, category, tags, published_at"


@router.get("/articles")
def list_articles(page: int = 1, per_page: int = 10, category: str = "",
                  tag: str = "", q: str = ""):
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
        f"SELECT {_FIELDS} FROM contents WHERE {w} ORDER BY published_at DESC LIMIT ? OFFSET ?",
        (*params, per_page, (page - 1) * per_page),
    )
    return {"items": items, "total": total, "page": page, "per_page": per_page,
            "category": category, "tag": tag, "q": q}


@router.get("/articles/{slug}")
def get_article(slug: str):
    row = db.query_one(
        f"SELECT {_FIELDS}, body FROM contents WHERE slug = ? AND status = 'published'",
        (slug,),
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artigo não encontrado")
    row["reading_time"] = reading_time_minutes(row["body"])
    return row


@router.get("/articles/{slug}/related")
def get_related(slug: str, limit: int = 3):
    return related_articles(slug, min(max(limit, 1), 6))


@router.get("/categories")
def list_categories():
    return db.query(
        """SELECT category, COUNT(*) AS total FROM contents
           WHERE status = 'published' AND category != ''
           GROUP BY category ORDER BY total DESC, category"""
    )


@router.get("/tags")
def list_tags():
    rows = db.query("SELECT tags FROM contents WHERE status = 'published' AND tags != ''")
    counter = Counter()
    for r in rows:
        counter.update(t for t in r["tags"].split(",") if t)
    return [{"tag": t, "total": n} for t, n in counter.most_common()]


@router.post("/contact", status_code=201)
def contact(data: ContactIn):
    """Formulário público de contato — mensagens aparecem nos Logs do admin."""
    db.execute(
        "INSERT INTO logs (level, source, message, meta_json) VALUES ('info','contato',?,?)",
        (f"Mensagem de {data.name}: {data.message[:200]}",
         json.dumps({"name": data.name, "email": data.email, "message": data.message})),
    )
    return {"ok": True, "detail": "Mensagem recebida. Obrigado pelo contato!"}


@router.post("/newsletter", status_code=201)
def newsletter_subscribe(data: ContactIn):
    """Inscrição na newsletter (usa name como segmento opcional)."""
    if not db.query_one("SELECT id FROM subscribers WHERE email = ?", (data.email,)):
        db.execute("INSERT INTO subscribers (email, segment) VALUES (?, 'geral')", (data.email,))
    return {"ok": True, "detail": "Inscrição confirmada!"}
