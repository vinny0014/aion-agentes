"""DISCOVERY GROWTH AGENT — arquitetura de crescimento orgânico.

Tudo que independe de credenciais funciona já; integrações externas (Search
Console, Analytics, AdSense, Trends, Bing, Cloudflare) têm a arquitetura pronta
e ficam registradas como pendência humana até as credenciais existirem.
Nada aqui promete resultados — o objetivo é maximizar as CHANCES de crescimento.
"""
import json
import math
import re
from collections import Counter

from ..core import database as db

WPM = 200  # palavras por minuto (leitura média em pt-BR)

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "um", "uma", "para",
    "com", "que", "por", "os", "as", "no", "na", "nos", "nas", "ao", "se",
    "sobre", "como", "mais", "ou", "são", "ser", "seu", "sua", "este", "esta",
}

INTEGRATIONS = {
    "google_search_console": {"env": "GSC_SITE_VERIFICATION", "status": "pendente-credencial"},
    "google_analytics": {"env": "VITE_GA_MEASUREMENT_ID", "status": "pendente-credencial"},
    "google_adsense": {"env": "VITE_ADSENSE_CLIENT", "status": "pendente-credencial"},
    "google_trends": {"env": "—", "status": "pendente-credencial"},
    "bing_webmaster": {"env": "BING_SITE_VERIFICATION", "status": "pendente-credencial"},
    "cloudflare_analytics": {"env": "VITE_CF_ANALYTICS_TOKEN", "status": "pendente-credencial"},
}


def reading_time_minutes(body: str) -> int:
    words = len(re.findall(r"\w+", body or ""))
    return max(1, math.ceil(words / WPM))


def extract_keywords(text: str, top: int = 8) -> list[str]:
    words = re.findall(r"[a-záàâãéêíóôõúç]{4,}", (text or "").lower())
    counter = Counter(w for w in words if w not in STOPWORDS)
    return [w for w, _ in counter.most_common(top)]


def related_articles(slug: str, limit: int = 3) -> list[dict]:
    """Cluster de conteúdo: relaciona por categoria e tags compartilhadas."""
    base = db.query_one(
        "SELECT id, category, tags FROM contents WHERE slug = ? AND status = 'published'", (slug,))
    if not base:
        return []
    rows = db.query(
        """SELECT id, title, slug, excerpt, category, tags, published_at
           FROM contents WHERE status = 'published' AND id != ?""", (base["id"],))
    base_tags = set(t for t in (base["tags"] or "").split(",") if t)
    scored = []
    for r in rows:
        score = 0
        if base["category"] and r["category"] == base["category"]:
            score += 2
        score += len(base_tags & set(t for t in (r["tags"] or "").split(",") if t))
        scored.append((score, r["published_at"] or "", r))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [r for _, __, r in scored[:limit]]


def editorial_calendar() -> list[dict]:
    """Calendário editorial: fila de conteúdo agendada + sugestões de cluster."""
    queue = db.query(
        """SELECT id, topic, template, status, scheduled_for FROM content_queue
           ORDER BY scheduled_for IS NULL, scheduled_for, id""")
    published = db.query("SELECT title, category, tags FROM contents WHERE status='published'")
    corpus = " ".join(f"{p['title']} {p['tags']}" for p in published)
    return {
        "fila": queue,
        "keywords_atuais": extract_keywords(corpus),
        "clusters": db.query(
            """SELECT category, COUNT(*) AS artigos FROM contents
               WHERE status='published' AND category != '' GROUP BY category"""),
        "recomendacao": "Publique diariamente e mantenha 2-3 artigos por cluster de categoria "
                        "com tags cruzadas para fortalecer a autoridade tópica.",
    }


def growth_report() -> dict:
    """Relatório do agente: estado das integrações + métricas internas."""
    stale = db.query(
        """SELECT id, title, slug, updated_at FROM contents
           WHERE status='published' AND updated_at < datetime('now', '-30 days')
           ORDER BY updated_at LIMIT 5""")
    if stale:
        db.execute(
            "INSERT INTO logs (level, source, message, meta_json) VALUES ('info','discovery-growth',?,?)",
            (f"{len(stale)} artigo(s) com mais de 30 dias — candidatos a atualização automática",
             json.dumps({"slugs": [s["slug"] for s in stale]})),
        )
    return {
        "agente": "discovery-growth",
        "integracoes": INTEGRATIONS,
        "conteudos_publicados": db.query_one(
            "SELECT COUNT(*) AS n FROM contents WHERE status='published'")["n"],
        "artigos_para_atualizar": stale,
        "calendario": editorial_calendar(),
        "observacao": "Integrações externas aguardam credenciais (ver PENDENCIAS_HUMANAS.md). "
                      "Nenhum resultado é garantido; a arquitetura maximiza as chances de crescimento.",
    }
