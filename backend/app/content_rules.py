"""Non-negotiable publication gates for the public English news site."""
import re

from .core import database as db
from .agents.imagegen import is_http_image_url, managed_image_path


PORTUGUESE_MARKERS = {
    "agentes", "ainda", "artigo", "artigos", "atualização", "cadastro", "categoria",
    "como", "com", "conteúdo", "da", "das", "de", "diário", "destaque", "do", "dos",
    "em", "entre", "inteligência", "leia", "mais", "melhores", "não", "notícia",
    "notícias", "novo", "para", "por", "publicação", "publicado", "que", "sobre",
    "termos", "uma", "você", "porque", "guia", "lança", "hoje",
}
PORTUGUESE_TAXONOMY = {
    "ia", "noticia", "noticias", "guia", "guias", "comparacao", "comparacoes",
    "fundamentos", "analise", "tecnologia", "saude", "educacao",
}


def looks_english(*parts: str) -> bool:
    text = " ".join(p or "" for p in parts).lower()
    words = re.findall(r"[a-záàâãéêíóôõúç]+", text)
    hits = len(set(words) & PORTUGUESE_MARKERS)
    return bool(words) and hits < 2


def publication_issues(content: dict) -> list[str]:
    issues: list[str] = []
    image_url = (content.get("image_url") or "").strip()
    if not is_http_image_url(image_url):
        issues.append("A verified HTTP/HTTPS raster image is required")
    elif image_url.startswith("data:") or image_url.lower().endswith(".svg"):
        issues.append("SVG, data URI and placeholder images cannot be published")
    elif managed_image_path(image_url) is None:
        issues.append("The publication image must be validated and stored by AION")
    if not looks_english(content.get("title", ""), content.get("excerpt", ""),
                         content.get("body", "")):
        issues.append("Public content must be written in English")
    taxonomy = set(re.findall(r"[a-z]+", f"{content.get('category', '')} {content.get('tags', '')}".lower()))
    if taxonomy & PORTUGUESE_TAXONOMY:
        issues.append("Public categories and tags must be written in English")
    return issues


def quarantine_noncompliant_public_content() -> dict:
    """Move legacy non-compliant rows back to draft during every startup."""
    quarantined: list[int] = []
    for row in db.query("SELECT * FROM contents WHERE status='published'"):
        issues = publication_issues(row)
        if issues:
            db.execute(
                "UPDATE contents SET status='draft', published_at=NULL, featured=0, "
                "pinned=0, breaking_flag=0 WHERE id=?",
                (row["id"],),
            )
            quarantined.append(row["id"])
            db.execute(
                "INSERT INTO logs(level,source,message,meta_json) VALUES "
                "('warn','publication-gate',?,?)",
                (f"Content #{row['id']} returned to draft", str(issues)),
            )
    return {"quarantined": quarantined, "count": len(quarantined)}
