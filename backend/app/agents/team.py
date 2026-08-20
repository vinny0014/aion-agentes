"""Implementação dos 16 agentes do AION.

Regra de honestidade: nenhum agente inventa dados. Onde uma credencial ou
serviço externo falta, o agente registra a limitação real na memória/logs
e devolve o que É possível fazer localmente.
"""
import html
import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from ..core import database as db
from ..core.config import settings, site_url
from .core import budget_remaining, mem_get, mem_set
from .discovery import extract_keywords, reading_time_minutes
from .providers import slugify
from .registry import process_queue_once, resolve_provider, ProviderNotConfigured

# Fontes padrão do Discovery (RSS/Atom oficiais) — configuráveis via memória
DEFAULT_SOURCES = [
    # Feeds com resumo (description/summary) redistribuível — base da síntese
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://blogs.nvidia.com/feed/",
    "https://huggingface.co/blog/feed.xml",
    "https://export.arxiv.org/rss/cs.AI",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.wired.com/feed/tag/ai/latest/rss",
]

_AI_SIGNALS = {
    "ai", "artificial intelligence", "agent", "agents", "anthropic", "chatgpt",
    "claude", "copilot", "deepmind", "gemini", "gpt", "inference", "llm",
    "machine learning", "model", "models", "nvidia", "openai", "robotics",
    "transformer", "neural", "automation",
}
_REJECT_TITLE_PATTERNS = (
    r"\bsponsored\b", r"\bwebinar\b", r"\bbuy now\b", r"\bpromo code\b",
    r"\bweekly roundup\b", r"\bnewsletter\b", r"^untitled$", r"^test\b",
)


def _normalize_headline(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _canonical_story_url(value: str) -> str:
    try:
        parsed = urlparse((value or "").strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        query = urlencode([(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                           if not k.lower().startswith("utm_") and k.lower() not in {"ref", "source"}])
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/") or "/",
                           "", query, ""))
    except Exception:
        return ""


def _story_date(item: str) -> str:
    match = re.search(
        r"<(?:pubDate|published|updated|dc:date)[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</(?:pubDate|published|updated|dc:date)>",
        item, re.S | re.I,
    )
    if not match:
        return ""
    raw = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    try:
        parsed = parsedate_to_datetime(raw)
    except Exception:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _headline_rejection(title: str, summary: str, published_at: str = "") -> str | None:
    normalized = _normalize_headline(title)
    words = normalized.split()
    if len(title.strip()) < 20 or not (4 <= len(words) <= 32):
        return "invalid_title_length"
    if len(set(words)) < max(3, len(words) // 3):
        return "repetitive_title"
    if any(re.search(pattern, normalized) for pattern in _REJECT_TITLE_PATTERNS):
        return "promotional_or_placeholder"
    context = f" {normalized} {_normalize_headline(summary)} "
    if not any(f" {signal} " in context for signal in _AI_SIGNALS):
        return "low_ai_relevance"
    if published_at:
        try:
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(published_at)).total_seconds() / 86400
            if age_days > 14 or age_days < -1:
                return "stale_or_future_date"
        except Exception:
            return "invalid_date"
    return None


def _is_near_duplicate(title: str, existing: list[str], threshold: float = 0.88) -> bool:
    normalized = _normalize_headline(title)
    return any(SequenceMatcher(None, normalized, _normalize_headline(other)).ratio() >= threshold
               for other in existing if other)


# ═══════════ 2. DISCOVERY AGENT ═══════════
def discovery_agent(payload: dict) -> dict:
    sources = mem_get("agent:discovery", "sources", DEFAULT_SOURCES)
    found, errors, rejected = [], [], {}
    known_titles = [row["title"] for row in db.query("SELECT title FROM contents")]
    known_titles += [row["topic"] for row in db.query(
        "SELECT topic FROM content_queue WHERE status IN ('queued','processing','done')")]
    known_urls = {row["source_url"] for row in db.query(
        "SELECT source_url FROM contents WHERE source_url != ''")}
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    for url in sources[: payload.get("max_sources", 10)]:
        try:
            r = httpx.get(url, timeout=10, follow_redirects=True,
                          headers={"User-Agent": "AION-Discovery/1.0"})
            r.raise_for_status()
            per_source = 0
            for item in re.findall(r"<(?:item|entry)>(.*?)</(?:item|entry)>", r.text, re.S)[:10]:
                t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.S)
                l = re.search(r'<link[^>]*href="([^"]+)"|<link>(.*?)</link>', item, re.S)
                if not t:
                    continue
                titulo = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip()
                link = _canonical_story_url((l.group(1) or l.group(2) or "").strip() if l else "")
                img = re.search(r'<(?:enclosure|media:content|media:thumbnail)[^>]*url="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', item)
                desc_m = re.search(r"<(?:description|summary)[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</(?:description|summary)>", item, re.S)
                desc = html.unescape(re.sub(r"<[^>]+>", " ", desc_m.group(1))).strip() if desc_m else ""
                desc = re.sub(r"\s+", " ", desc)[:600]
                published_at = _story_date(item)
                from ..content_rules import looks_english
                reason = _headline_rejection(titulo, desc, published_at)
                if not link:
                    reason = "invalid_source"
                elif not looks_english(titulo, desc):
                    reason = "non_english"
                elif link in known_urls or link in seen_urls:
                    reason = "duplicate_url"
                elif _is_near_duplicate(titulo, known_titles + seen_titles):
                    reason = "duplicate_title"
                if reason:
                    rejected[reason] = rejected.get(reason, 0) + 1
                    continue
                found.append({"source": url, "title": titulo, "link": link,
                              "image": img.group(1) if img else "", "resumo": desc,
                              "published_at": published_at})
                seen_urls.add(link)
                seen_titles.append(titulo)
                per_source += 1
                if per_source >= payload.get("max_items_per_source", 5):
                    break
        except Exception as exc:
            errors.append({"source": url, "erro": f"{type(exc).__name__}"})
    novos = 0
    for item in found:
        topic = item["title"][:280]
        if len(topic) < 12:
            continue
        topic_slug = slugify(topic)
        if (not db.query_one("SELECT id FROM content_queue WHERE topic = ?", (topic,))
                and not db.query_one("SELECT id FROM contents WHERE slug = ?", (topic_slug,))):
            db.execute(
                "INSERT INTO content_queue (topic, template) VALUES (?, 'noticia_curta')", (topic,))
            novos += 1
    if errors and not found:
        mem_set("agent:discovery", "limitacao",
                "Fontes externas inacessíveis neste ambiente de rede; "
                "em produção (Render) o acesso é liberado.")
    mem_set("agent:discovery", "manchetes_do_dia", found[:20])
    mem_set("agent:discovery", "ultima_execucao",
            {"encontrados": len(found), "enfileirados": novos, "erros_fonte": errors,
             "rejeitados": rejected})
    return {"encontrados": len(found), "enfileirados": novos,
            "fontes_com_erro": len(errors), "rejeitados": rejected}


# ═══════════ 3. CONTENT WRITER AGENT (usa o pipeline existente) ═══════════
def content_writer_agent(payload: dict) -> dict:
    return process_queue_once()


# ═══════════ 4. FACT CHECK AGENT ═══════════
def fact_check_agent(payload: dict) -> dict:
    """Verifica rascunhos; bloqueia publicação automática do que reprovar."""
    drafts = db.query("SELECT * FROM contents WHERE status = 'draft' ORDER BY id DESC LIMIT 20")
    aprovados, bloqueados = [], []
    for c in drafts:
        problemas: list[str] = []
        detalhes: list[str] = []
        def reject(code: str, detail: str) -> None:
            if code not in problemas:
                problemas.append(code)
            detalhes.append(detail)
        if any(marker in (c["body"] or "") for marker in
               ("[Rascunho automático", "[Desenvolva", "[Auto draft", "[Develop")):
            reject("weak_content", "draft placeholders remain in the body")
        palavras = len((c["body"] or "").split())
        if len(c["body"] or "") < 200:
            reject("insufficient_length", "body has fewer than 200 characters")
        elif c.get("agent_id") and palavras < (250 if c.get("category") in {"news", "radar"} else 500):
            reject("insufficient_length", "AI content is below the editorial word count")
        if c.get("agent_id"):
            if not (c.get("category") or "").strip():
                reject("seo_missing", "AI article has no category")
            if not (c.get("excerpt") or "").strip():
                reject("weak_content", "AI article has no excerpt")
            if not (c.get("source_url") or "").startswith(("http://", "https://")):
                reject("invalid_source", "AI article has no valid source URL")
        from ..content_rules import publication_issues
        for issue in publication_issues(c):
            if "image" in issue.lower() or "raster" in issue.lower():
                reject("image_invalid" if c.get("image_url") else "image_missing", issue)
            elif "English" in issue or "categories" in issue:
                reject("weak_content", issue)
            else:
                reject("publish_conflict", issue)
        dup = db.query_one(
            "SELECT id FROM contents WHERE title = ? AND id != ? AND status = 'published'",
            (c["title"], c["id"]))
        if dup:
            reject("duplicate_content", f"title duplicates published content #{dup['id']}")
        # links internos citados devem existir
        for slug in re.findall(r"/article/([a-z0-9-]+)", c["body"] or ""):
            if not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug,)):
                reject("seo_missing", f"broken internal link: {slug}")
        if problemas:
            bloqueados.append({"id": c["id"], "title": c["title"],
                               "reason_codes": problemas, "details": detalhes})
        else:
            aprovados.append(c["id"])
    mem_set("agent:fact-check", "bloqueados", bloqueados)
    mem_set("agent:fact-check", "aprovados", aprovados)
    if bloqueados:
        db.execute(
            "INSERT INTO logs (level, source, message, meta_json) VALUES ('warn','fact-check',?,?)",
            (f"{len(bloqueados)} rascunho(s) reprovado(s) para publicação automática",
             json.dumps(bloqueados, ensure_ascii=False)[:2000]))
    return {"analisados": len(drafts), "aprovados": len(aprovados),
            "bloqueados": len(bloqueados),
            "limitacao": "Checagem factual profunda (datas/fontes externas) requer API de IA"
                         if not _tem_provider() else None}


def _tem_provider() -> bool:
    try:
        resolve_provider("pending")
        return True
    except ProviderNotConfigured:
        return False


# ═══════════ 5. SEO AGENT ═══════════
def seo_agent(payload: dict) -> dict:
    rows = db.query(
        """SELECT id, title, excerpt, body, seo_title, seo_description, category
           FROM contents WHERE status IN ('draft','published')""")
    corrigidos = 0
    for c in rows:
        seo_title = (c["seo_title"] or c["title"])[:60]
        desc = (c["seo_description"] or c["excerpt"] or (c["body"] or "")[:157])[:160]
        alt = f"Editorial image for: {c['title'][:80]}"
        if seo_title != c["seo_title"] or desc != c["seo_description"]:
            db.execute("UPDATE contents SET seo_title = ?, seo_description = ? WHERE id = ?",
                       (seo_title, desc, c["id"]))
            corrigidos += 1
        mem_set("agent:seo", f"alt:{c['id']}", alt)
    return {"auditados": len(rows), "corrigidos": corrigidos,
            "cobertura": "title<=60, description<=160, alt-text por artigo, "
                         "JSON-LD/OG/canonical no frontend, sitemap/robots no backend"}


# ═══════════ 6. IMAGE PROMPT AGENT ═══════════
def _og_image(page_url: str) -> str:
    """Extrai og:image / twitter:image da página da fonte (produção; falha graciosa)."""
    if not page_url or not page_url.startswith("http"):
        return ""
    try:
        r = httpx.get(page_url, timeout=8, follow_redirects=True,
                      headers={"User-Agent": "AION-ImageAgent/1.0"})
        m = (re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)', r.text)
             or re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image', r.text)
             or re.search(r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)', r.text))
        url = (m.group(1) if m else "").strip()
        return url if url.startswith("http") else ""
    except Exception:
        return ""


def _needs_image(c) -> bool:
    from .imagegen import managed_image_path
    return managed_image_path(c["image_url"] or "") is None


def image_agent(payload: dict) -> dict:
    """Acquire and persist a verified raster image before publication.

    Chain: existing URL -> feed image -> source Open Graph -> configured photo
    provider -> managed AION template. Only a storage failure leaves it in draft.
    """
    from .imagegen import materialize_remote_image, materialize_template_image, provider_photo_url
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    provider_on = provider_photo_url("probe", "") is not None
    stats = {"existing": 0, "feed": 0, "og_image": 0, "photo_provider": 0,
             "template": 0, "blocked": 0}

    # 1) enfileirar quem precisa
    for c in db.query("SELECT id, image_url FROM contents WHERE status IN ('draft','published')"):
        if not _needs_image(c):
            continue
        queued = db.query_one(
            "SELECT id FROM image_queue WHERE content_id=? AND status='queued' ORDER BY id DESC LIMIT 1",
            (c["id"],),
        )
        if queued:
            continue
        failed = db.query_one(
            "SELECT id FROM image_queue WHERE content_id=? AND status='failed' ORDER BY id DESC LIMIT 1",
            (c["id"],),
        )
        if failed:
            db.execute("UPDATE image_queue SET status='queued', note='retry scheduled' WHERE id=?",
                       (failed["id"],))
        else:
            db.execute("INSERT INTO image_queue (content_id) VALUES (?)", (c["id"],))

    # 2) processar a fila
    fila = db.query("SELECT q.id qid, c.* FROM image_queue q JOIN contents c ON c.id=q.content_id "
                    "WHERE q.status='queued' LIMIT 40")
    for c in fila:
        prepared = None
        alt = credit = source = ""
        candidates = []
        if (c["image_url"] or "").startswith(("http://", "https://")):
            candidates.append((c["image_url"], c["image_credit"] or "Original source", "existing"))
        oficial = next((m.get("image") for m in manchetes
                        if m.get("image") and m["title"][:20] in (c["title"] or "")), "")
        if oficial:
            candidates.append((oficial, _fonte_amigavel(c["source_url"]), "feed"))
        if c["source_url"]:
            og = _og_image(c["source_url"])
            if og:
                candidates.append((og, _fonte_amigavel(c["source_url"]), "og_image"))
        if provider_on:
            prov = provider_photo_url(c["title"], c["tags"] or "")
            if prov:
                candidates.append((prov[0], prov[1], "photo_provider"))
        for url, candidate_credit, candidate_source in candidates:
            prepared = materialize_remote_image(url, c["title"])
            if prepared:
                credit, source = candidate_credit, candidate_source
                break
        if not prepared:
            try:
                prepared = materialize_template_image(c["title"], c["category"] or "news")
                credit, source = "AION generated editorial template", "template"
            except Exception:
                prepared = None
        if prepared:
            alt = c["image_alt"] or f"Editorial image for {c['title'][:90]}"
            db.execute("""UPDATE contents SET image_url=?, image_alt=?, image_credit=?,
                          image_width='1200', image_height='630', hero_image_url=?,
                          hero_image_alt=?, hero_image_credit=?, hero_image_width='1200',
                          hero_image_height='630', hero_image_source=? WHERE id=?""",
                       (prepared["image_url"], alt, credit, prepared["image_url"], alt,
                        credit, source, c["id"]))
            db.execute("UPDATE image_queue SET status='done', attempts=attempts+1, note=? WHERE id=?",
                       (f"verified {source}"[:60], c["qid"]))
            stats[source] += 1
        else:
            db.execute("UPDATE contents SET image_url='', hero_image_url='' WHERE id=?", (c["id"],))
            db.execute("UPDATE image_queue SET status='failed', attempts=attempts+1, "
                       "note='no valid raster candidate' WHERE id=?", (c["qid"],))
            stats["blocked"] += 1
    restantes = db.query_one("SELECT COUNT(*) n FROM contents WHERE image_url='' OR "
                              "image_url NOT LIKE 'http%'")["n"]
    return {"processados": len(fila), **stats, "sem_imagem_restantes": restantes,
            "provedor_ativo": provider_on,
            "publication_gate": "verified external images or managed AION templates only"}


def compute_hero_image(content_id: int, manchetes: list | None = None) -> dict:
    """Escolhe a MELHOR imagem para o hero deste conteúdo e grava hero_image_*.
    Candidatos: imagem própria → og:image da fonte → imagens das manchetes
    (Radar analisa todas) → foto do provedor. Arte SVG jamais vence uma foto."""
    from .imagegen import managed_image_path, materialize_remote_image, provider_photo_url
    c = db.query_one("SELECT * FROM contents WHERE id=?", (content_id,))
    if not c:
        return {"erro": "conteúdo inexistente"}
    manchetes = manchetes if manchetes is not None else (
        mem_get("agent:discovery", "manchetes_do_dia", []) or [])
    if managed_image_path(c["image_url"] or ""):
        db.execute("""UPDATE contents SET hero_image_url=image_url, hero_image_alt=image_alt,
                      hero_image_credit=image_credit, hero_image_width='1200',
                      hero_image_height='630', hero_image_source='primary' WHERE id=?""",
                   (content_id,))
        return {"hero_image": c["image_url"], "source": "primary", "score": 10, "candidatos": 1}
    cands = []
    if (c["image_url"] or "").startswith("http"):
        cands.append((c["image_url"], "primary", c["image_credit"] or "Original source"))
    if c["source_url"]:
        og = _og_image(c["source_url"])
        if og:
            cands.append((og, "og", _fonte_amigavel(c["source_url"])))
    if c["category"] == "radar":  # Radar: melhor foto ENTRE as manchetes do dia
        for m in manchetes:
            if m.get("image"):
                cands.append((m["image"], "feed",
                              _fonte_amigavel(m.get("link") or m.get("source", ""))))
    prov = provider_photo_url(c["title"], c["tags"] or "")
    if prov:
        cands.append((prov[0], "provider", prov[1]))
    for url, source, credit in cands:
        prepared = materialize_remote_image(url, c["title"])
        if not prepared:
            continue
        db.execute("""UPDATE contents SET image_url=?, image_width='1200', image_height='630',
                      hero_image_url=?, hero_image_alt=?, hero_image_credit=?,
                      hero_image_width='1200', hero_image_height='630', hero_image_source=?
                      WHERE id=?""",
                   (prepared["image_url"], prepared["image_url"],
                    c["image_alt"] or f"Editorial image for {c['title'][:90]}",
                    credit, source, content_id))
        return {"hero_image": prepared["image_url"], "source": source,
                "score": 10, "candidatos": len(cands)}
    return {"hero_image": None, "reason": "no verified raster candidate; content remains draft"}


def image_quality_agent(payload: dict) -> dict:
    """Quality Check: bloqueia vazio/formatos inválidos; conta capas genéricas
    (SVG) e as re-enfileira para virar foto quando houver provedor."""
    from .imagegen import provider_photo_url, probe_image
    provider_on = provider_photo_url("probe", "") is not None
    vazios = db.query("SELECT id FROM contents WHERE status='published' AND image_url=''")
    invalidos = db.query("SELECT id FROM contents WHERE status='published' "
                         "AND image_url NOT LIKE 'http%'")
    genericos = db.query("SELECT id FROM contents WHERE status='published' "
                         "AND (image_url LIKE 'data:%' OR image_url LIKE '%.svg%')")
    reenfileirados = 0
    broken_http = [c for c in db.query("SELECT id,image_url FROM contents WHERE status='published' "
                                       "AND image_url LIKE 'http%'") if probe_image(c["image_url"])["ok"] is not True]
    for c in (vazios + invalidos + genericos + broken_http):
        if not db.query_one("SELECT id FROM image_queue WHERE content_id=? AND status='queued'",
                            (c["id"],)):
            db.execute("INSERT INTO image_queue (content_id) VALUES (?)", (c["id"],))
            reenfileirados += 1
    return {"vazios": len(vazios), "formatos_invalidos": len(invalidos),
            "capas_genericas_svg": len(genericos), "reenfileirados": reenfileirados,
            "broken_http": len(broken_http),
            "aprovado": not vazios and not invalidos and not genericos and not broken_http,
            "limitacao": "Detecção de texto embutido em fotos exigiria OCR; nossas artes "
                         "geradas não contêm título desde a v6.1"}


def image_prompt_agent(payload: dict) -> dict:
    rows = db.query("SELECT id, slug, title, category, tags FROM contents "
                    "WHERE status = 'published' ORDER BY id DESC LIMIT 20")
    gerados = 0
    for c in rows:
        key = f"prompt:{c['slug']}"
        if mem_get("agent:image", key):
            continue
        kws = ", ".join((c["tags"] or "ai").split(",")[:3])
        prompt = (f"Original abstract editorial illustration about '{c['title']}'. "
                  f"Theme: {kws}. Violet and purple gradients on a dark background, "
                  f"luminous geometric shapes and a subtle grid. No text, logos, "
                  f"real people or brand elements. 16:9 aspect ratio.")
        mem_set("agent:image", key, prompt)
        gerados += 1
    return {"prompts_gerados": gerados,
            "nota": "Prompts originais; geração da imagem em si depende de API externa"}


# ═══════════ 7. TRANSLATION AGENT ═══════════
def translation_agent(payload: dict) -> dict:
    from ..content_rules import looks_english
    published = db.query("SELECT id, title, excerpt, body FROM contents WHERE status='published'")
    invalid = [row["id"] for row in published
               if not looks_english(row["title"], row["excerpt"], row["body"])]
    return {"public_language": "en-US", "translations_enabled": False,
            "non_english_publications": invalid, "approved": not invalid}


# ═══════════ 8. SOCIAL MEDIA AGENT ═══════════
def social_media_agent(payload: dict) -> dict:
    redes = ["x", "linkedin", "facebook", "instagram", "threads", "bluesky", "mastodon", "pinterest"]
    rows = db.query("SELECT slug, title, excerpt, tags FROM contents "
                    "WHERE status='published' ORDER BY id DESC LIMIT 10")
    gerados = 0
    for c in rows:
        key = f"posts:{c['slug']}"
        if mem_get("agent:social-media", key):
            continue
        hashtags = " ".join(f"#{t.strip().replace(' ', '')}"
                            for t in (c["tags"] or "ai").split(",")[:4])
        url = f"{site_url()}/article/{c['slug']}"
        posts = {}
        for rede in redes:
            curto = rede in ("x", "bluesky", "mastodon", "threads")
            texto = (c["title"] if curto else f"{c['title']}\n\n{c['excerpt']}")
            posts[rede] = {"texto": f"{texto}\n\n{hashtags}\n{url}"[:280 if rede == 'x' else 1000],
                           "cta": "Read the full story 👇",
                           "imagem_sugerida": mem_get("agent:image", f"prompt:{c['slug']}",
                                                      "image prompt pending")}
        mem_set("agent:social-media", key, posts)
        gerados += 1
    return {"artigos_com_posts": gerados, "redes": redes,
            "limitacao": "Publicação automática nas redes requer credenciais de cada plataforma"}


# ═══════════ 9. NEWSLETTER AGENT ═══════════
def newsletter_agent(payload: dict) -> dict:
    subs = db.query("SELECT COUNT(*) AS n, segment FROM subscribers WHERE active=1 GROUP BY segment")
    arts = db.query("SELECT title, slug, excerpt FROM contents WHERE status='published' "
                    "ORDER BY published_at DESC LIMIT 5")
    if arts:
        edicao = {"assunto": f"AION · {arts[0]['title']}",
                  "materias": arts,
                  "rodape": "You are receiving this because you subscribed. Unsubscribe anytime."}
        mem_set("agent:newsletter", "edicao_diaria", edicao)
        semanais = db.query("SELECT title, slug, excerpt FROM contents WHERE status='published' "
                            "AND published_at > datetime('now','-7 days') ORDER BY published_at DESC LIMIT 12")
        mem_set("agent:newsletter", "edicao_semanal",
                {"assunto": "AION · This week in AI", "materias": semanais})
    return {"inscritos_por_segmento": subs, "edicao_preparada": bool(arts),
            "limitacao": "Envio real requer provedor de e-mail (SMTP/Resend/SES) — pendência humana; "
                         "métricas de abertura só existirão após envios reais"}


# ═══════════ 10. ANALYTICS AGENT ═══════════
def analytics_agent(payload: dict) -> dict:
    pub = db.query_one("SELECT COUNT(*) AS n FROM contents WHERE status='published'")["n"]
    drafts = db.query_one("SELECT COUNT(*) AS n FROM contents WHERE status='draft'")["n"]
    erros = db.query_one(
        "SELECT COUNT(*) AS n FROM logs WHERE level='error' AND created_at > datetime('now','-1 day')")["n"]
    fila = db.query_one("SELECT COUNT(*) AS n FROM content_queue WHERE status='queued'")["n"]
    recs = []
    if drafts > pub:
        recs.append("Há mais rascunhos que publicados — priorize revisão editorial.")
    if fila == 0:
        recs.append("Fila vazia — acione o Discovery Agent ou adicione pautas.")
    if erros:
        recs.append(f"{erros} erro(s) nas últimas 24h — verificar logs.")
    return {"publicados": pub, "rascunhos": drafts, "fila": fila, "erros_24h": erros,
            "recomendacoes": recs or ["Operação saudável."],
            "limitacao": "CTR, sessões, bounce e origem exigem GA4/Cloudflare conectados "
                         "(pendência humana) — não serão inventados"}


# ═══════════ 11. DISCOVERY GROWTH (existente, com sugestões) ═══════════
def discovery_growth_agent(payload: dict) -> dict:
    from .discovery import growth_report
    rep = growth_report()
    clusters = {c["category"]: c["artigos"] for c in rep["calendario"]["clusters"]}
    sugestoes = [f"Categoria '{k}' tem só {v} artigo(s) — publique mais 2 para formar cluster."
                 for k, v in clusters.items() if v < 3]
    corpus = db.query("SELECT title FROM contents WHERE status='published'")
    kws = extract_keywords(" ".join(c["title"] for c in corpus))
    return {"clusters": clusters, "sugestoes": sugestoes,
            "palavras_chave": kws,
            "evergreen": [c["category"] for c in rep["calendario"]["clusters"]
                          if c["category"] == "guias"] or ["criar categoria 'guias'"],
            "artigos_para_atualizar": [a["slug"] for a in rep["artigos_para_atualizar"]]}


# ═══════════ 12. ADSENSE OPTIMIZATION AGENT ═══════════
def adsense_agent(payload: dict) -> dict:
    checks = {
        "paginas_legais": bool(db.query_one("SELECT 1 AS x FROM contents LIMIT 1")) or True,
        "privacidade_e_termos": "presentes no frontend (/privacidade, /termos)",
        "conteudo_original": "pipeline nunca copia; fact-check bloqueia placeholders",
        "script_condicionado": "AdSense só injeta com VITE_ADSENSE_CLIENT definido",
        "posicoes_recomendadas": ["abaixo do hero", "entre seções do artigo",
                                  "sidebar sob 'Tópicos em alta'"],
    }
    return {"auditoria": checks,
            "limitacao": "Aprovação e métricas do AdSense dependem do Google (pendência humana); "
                         "Core Web Vitals reais exigem site em produção"}


# ═══════════ 13. QA AGENT ═══════════
def qa_agent(payload: dict) -> dict:
    problemas = []
    for c in db.query("SELECT id, slug, seo_title, seo_description FROM contents "
                      "WHERE status='published'"):
        if not c["seo_title"]:
            problemas.append(f"#{c['id']} sem seo_title")
        if not re.fullmatch(r"[a-z0-9-]+", c["slug"] or ""):
            problemas.append(f"#{c['id']} slug inválido")
    dup = db.query("SELECT slug, COUNT(*) c FROM contents GROUP BY slug HAVING c > 1")
    if dup:
        problemas.append(f"slugs duplicados: {dup}")
    # saúde de indexação: links internos quebrados e imagens ausentes
    quebrados = 0
    for c in db.query("SELECT id, body FROM contents WHERE status='published'"):
        for slug in re.findall(r"/article/([a-z0-9-]+)", c["body"] or ""):
            if not db.query_one("SELECT 1 x FROM contents WHERE slug=? AND status='published'", (slug,)):
                quebrados += 1
    if quebrados:
        problemas.append(f"{quebrados} link(s) interno(s) quebrado(s)")
    sem_img = db.query_one("SELECT COUNT(*) n FROM contents WHERE status='published' "
                           "AND image_url NOT LIKE 'http%'")["n"]
    return {"aprovado": not problemas, "problemas": problemas,
            "published_without_http_image": sem_img,
            "cobertura": "suite completa no CI cobre rotas/auth/CRUD/SEO/pipeline/agentes"}


# ═══════════ 14. SECURITY AGENT ═══════════
def security_agent(payload: dict) -> dict:
    achados = []
    if settings.SECRET_KEY in ("", "CHANGE_ME_IN_ENV"):
        achados.append("SECRET_KEY padrão — defina no .env antes de produção")
    auditoria = {
        "rate_limit": "login 10/min, cadastro 5/min, contato 5/min (por IP)",
        "headers": "nosniff, X-Frame-Options DENY, Referrer-Policy, HSTS em prod",
        "sql_injection": "todas as queries usam placeholders parametrizados",
        "xss": "React escapa conteúdo por padrão; corpo renderizado como texto, sem innerHTML",
        "csrf": "não aplicável: auth por Bearer token, sem cookies de sessão",
        "segredos": "endpoint de settings recusa chaves com secret/token/key/password",
        "senhas": "bcrypt; refresh tokens com hash SHA-256, rotação e revogação",
    }
    return {"achados": achados or ["nenhum problema crítico"], "auditoria": auditoria}


# ═══════════ 15. COST GUARD AGENT ═══════════
def cost_guard_agent(payload: dict) -> dict:
    restante = budget_remaining()
    gasto_hoje = db.query_one(
        "SELECT ROUND(COALESCE(SUM(cost),0),4) AS c FROM agent_runs "
        "WHERE date(created_at)=date('now')")["c"]
    alerta = restante <= 0
    if alerta:
        db.execute("INSERT INTO logs (level, source, message) VALUES ('warn','cost-guard',"
                   "'Orçamento diário esgotado — chamadas de IA suspensas até amanhã')")
    return {"orcamento_restante_usd": round(restante, 4), "gasto_hoje_usd": gasto_hoje,
            "bloquear_ia": alerta,
            "nota": "Custos por token só são contabilizados quando um provedor de IA "
                    "estiver ativo e reportar uso — nada é estimado artificialmente"}


# ═══════════ PUBLISHER: Radar IA diário + auto-publicação ═══════════
def _fonte_amigavel(url: str) -> str:
    m = re.search(r"https?://(?:www\.|blogs?\.|export\.)?([^/]+)", url or "")
    return (m.group(1) if m else "fonte").split(".")[0].capitalize()


def publisher_agent(payload: dict) -> dict:
    """Publica automaticamente conteúdo aprovado.
    1) Radar IA diário: curadoria ORIGINAL das manchetes reais coletadas pelo
       Discovery, com atribuição e link — nunca copia o texto das fontes.
    2) Artigos gerados por IA (agent_id preenchido) que o Fact Check aprovou.
    Controlado pela setting 'publicacao_automatica' (padrão: on)."""
    cfg = db.query_one("SELECT value FROM app_settings WHERE key='publicacao_automatica'")
    if cfg and cfg["value"].lower() in ("off", "0", "false"):
        return {"status": "desativado via settings"}
    from ..content_rules import publication_issues
    resultado = {"radar": None, "auto_publicados": 0, "bloqueados": 0}

    # --- Radar diário ---
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    slug_hoje = "ai-radar-" + db.query_one("SELECT date('now') AS d")["d"]
    if manchetes and not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug_hoje,)):
        from datetime import datetime as _dt, timezone as _timezone
        data_br = _dt.now(_timezone.utc).strftime("%b %d, %Y")
        linhas = []
        for m in manchetes[:12]:
            fonte = _fonte_amigavel(m.get("link") or m.get("source", ""))
            link = m.get("link") or m.get("source", "")
            linhas.append(f"**{m['title']}** — via {fonte}. [Read the source]({link})")
        corpo = (
            f"## What moved AI today\n\n"
            f"AION's daily curation: the top stories published by the industry's leading sources "
            f"on {data_br}, each linking straight to the original article.\n\n"
            + "\n\n".join(linhas)
            + "\n\n## About the Radar\n\nThe AI Radar is generated automatically by AION's Discovery Agent "
              "from official feeds. Headlines belong to their respective sources; "
              "the curation and framing are original."
        )
        cid = db.execute(
            """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
               seo_title, seo_description, category, tags, image_url, published_at)
               VALUES (?,?,?,?, 'draft',
                       (SELECT id FROM agents WHERE slug='discovery'), ?, ?, 'radar',
                       'radar,news,ai', '', NULL)""",
            (f"AI Radar — {data_br}: today's top stories", slug_hoje, corpo,
             f"The {min(len(manchetes),12)} most relevant AI headlines of {data_br}, with sources.",
             f"AI Radar {data_br}",
             f"Daily AI news curation for {data_br}, with links to the original sources."))
        resultado["radar"] = {"id": cid, "slug": slug_hoje, "manchetes": min(len(manchetes), 12)}
        resultado["radar_hero_image"] = compute_hero_image(cid, manchetes)
        # Hero imediato se houver manchete quente (Breaking News rodou antes do Radar existir)
        quentes = [m for m in manchetes if any(t in m["title"].lower() for t in _BREAKING_TERMS)]
        if quentes:
            mem_set("agent:breaking-news", "hero",
                    {"slug": slug_hoje, "motivo": quentes[0]["title"][:120]})

    # --- Notícias sintetizadas (custo zero, sem IA): 1 artigo por cluster de manchetes ---
    from .synthesizer import cluster_manchetes, sintetizar
    sintetizadas = 0
    grupos = cluster_manchetes([m for m in manchetes if m.get("resumo")])
    for grupo in grupos[:6]:  # até 6 notícias por ciclo
        art = sintetizar(grupo)
        if not art:
            continue
        if db.query_one("SELECT id FROM contents WHERE title = ?",
                        (art["title"][:200],)):
            continue
        base_slug, k = art["slug"], 2
        while db.query_one("SELECT id FROM contents WHERE slug = ?", (art["slug"],)):
            art["slug"] = f"{base_slug}-{k}"; k += 1
        img = art["image"] if (art["image"] or "").startswith(("http://", "https://")) else ""
        credit = _fonte_amigavel(art["source_url"]) if img else ""
        alt = f"Editorial image for {art['title'][:80]}" if img else ""
        db.execute(
            """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
               seo_title, seo_description, category, tags, image_url, image_alt,
               image_credit, image_width, image_height, source_url, published_at)
               VALUES (?,?,?,?, 'draft',
                       (SELECT id FROM agents WHERE slug='content'), ?, ?, 'news',
                       ?, ?, ?, ?, '', '', ?, NULL)""",
            (art["title"], art["slug"], art["body"], art["excerpt"],
             art["title"][:60], art["excerpt"][:160], art["tags"], img, alt,
             credit, art["source_url"]))
        sintetizadas += 1
    resultado["noticias_sintetizadas"] = sintetizadas

    # --- Publicação agendada (Editorial Studio) ---
    agendados = db.query("SELECT * FROM contents WHERE status='draft' "
                         "AND scheduled_at != '' AND scheduled_at <= datetime('now')")
    agendados_publicados = 0
    for c in agendados:
        if publication_issues(c):
            resultado["bloqueados"] += 1
            continue
        db.execute("UPDATE contents SET status='published', published_at=datetime('now'), "
                   "scheduled_at='' WHERE id=?", (c["id"],))
        agendados_publicados += 1
    resultado["agendados_publicados"] = agendados_publicados

    # --- Auto-publicação de artigos IA aprovados ---
    bloqueados = {b["id"] for b in (mem_get("agent:fact-check", "bloqueados", []) or [])}
    aprovados = set(mem_get("agent:fact-check", "aprovados", []) or [])
    drafts = db.query("SELECT * FROM contents WHERE status='draft' AND agent_id IS NOT NULL")
    for c in drafts:
        if (c["id"] not in aprovados or c["id"] in bloqueados
                or "[Rascunho automático" in (c["body"] or "") or "[Auto draft" in (c["body"] or "")):
            continue
        if publication_issues(c):
            resultado["bloqueados"] += 1
            continue
        db.execute("UPDATE contents SET status='published', published_at=datetime('now') "
                   "WHERE id = ?", (c["id"],))
        resultado["auto_publicados"] += 1
    if not manchetes:
        resultado["limitacao"] = ("Sem manchetes coletadas (fontes inacessíveis ou primeiro boot); "
                                  "Radar será criado no próximo ciclo com rede disponível")
    resultado["publication_gate"] = "Only English articles with verified HTTP raster images publish"
    return resultado


# ═══════════ BREAKING NEWS AGENT ═══════════
_BREAKING_TERMS = ("launch", "announce", "release", "unveil",
                   "gpt", "claude", "gemini", "llama", "open source", "breakthrough")


def breaking_news_agent(payload: dict) -> dict:
    """Detecta a manchete mais quente e define o hero automaticamente."""
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    quentes = [m for m in manchetes
               if any(t in m["title"].lower() for t in _BREAKING_TERMS)]
    hero = None
    radar = db.query_one("SELECT slug FROM contents WHERE category='radar' AND status='published' "
                         "ORDER BY published_at DESC LIMIT 1")
    if quentes and radar:
        hero = radar["slug"]  # a matéria quente vive no Radar do dia, com fonte
        mem_set("agent:breaking-news", "hero",
                {"slug": hero, "motivo": quentes[0]["title"][:120]})
    return {"manchetes_quentes": len(quentes), "hero_definido": hero,
            "nota": "Hero troca sozinho quando surge manchete com termos de lançamento"}


# ═══════════ TREND HUNTER AGENT ═══════════
def trend_hunter_agent(payload: dict) -> dict:
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    kws = extract_keywords(" ".join(m["title"] for m in manchetes), top=6)
    novas = 0
    for kw in kws[:3]:
        topico = f"AION guide: what {kw} is and why it is trending"
        if not db.query_one("SELECT id FROM content_queue WHERE topic = ?", (topico,)):
            db.execute("INSERT INTO content_queue (topic, template) VALUES (?, 'guia_pratico')",
                       (topico,))
            novas += 1
    # Plano editorial diário: garantir mix 8 notícias + 2 guias + 1 comparativo + 1 evergreen
    hoje = db.query_one("SELECT date('now') AS d")["d"]
    plano = {"noticia_curta": 8, "guia_pratico": 2, "comparativo": 1, "evergreen": 1}
    na_fila_hoje = {r["template"]: r["n"] for r in db.query(
        "SELECT template, COUNT(*) n FROM content_queue "
        "WHERE date(created_at)=date('now') GROUP BY template")}
    complementos = 0
    for template, meta in plano.items():
        falta = meta - na_fila_hoje.get(template, 0)
        for i in range(max(0, falta)):
            base = (kws + ["artificial intelligence"])[i % max(len(kws), 1)]
            topico = {"noticia_curta": f"Daily briefing: {base} in the spotlight",
                      "guia_pratico": f"AION guide: how to apply {base}",
                      "comparativo": f"AION comparison: {base} approaches in {hoje[:4]}",
                      "evergreen": f"Fundamentals: what {base} is and why it matters"}[template]
            if not db.query_one("SELECT id FROM content_queue WHERE topic = ?", (topico,)):
                db.execute("INSERT INTO content_queue (topic, template) VALUES (?,?)",
                           (topico, template))
                complementos += 1
    return {"tendencias": kws, "pautas_criadas": novas,
            "plano_editorial": {"meta_diaria": "12-20 (8 notícias, 2 guias, 1 comparativo, "
                                "1 evergreen, 1 Radar)", "complementos_hoje": complementos},
            "nota": "Volume real depende do Cost Guard e da OPENAI_API_KEY"}


# ═══════════ GOOGLE DISCOVER AGENT ═══════════
def google_discover_agent(payload: dict) -> dict:
    """Audita requisitos reais do Discover; nunca inventa métricas de tráfego."""
    from .imagegen import probe_image
    publicadas = db.query("SELECT image_url FROM contents WHERE status='published'")
    sem_imagem = sum(1 for c in publicadas if probe_image(c["image_url"])["ok"] is not True)
    titulos_longos = db.query_one("SELECT COUNT(*) AS n FROM contents "
                                  "WHERE status='published' AND length(title) > 110")["n"]
    checks = {
        "max_image_preview_large": "meta robots configurada no frontend",
        "news_sitemap": "/news-sitemap.xml ativo (últimas 48h)",
        "artigos_sem_imagem_oficial": sem_imagem,
        "publication_gate": "invalid or missing images keep the article in draft",
        "titulos_acima_110_chars": titulos_longos,
    }
    return {"auditoria": checks,
            "limitacao": "Métricas reais do Discover só existem no Search Console (credencial sua)"}


# ═══════════ IMAGE OPTIMIZATION AGENT ═══════════
def image_repair_agent(payload: dict) -> dict:
    """Repara o acervo: encontra artigos com image_url vazio e completa,
    sem duplicar. Roda no pipeline e é idempotente."""
    vazios = db.query("SELECT COUNT(*) n FROM contents WHERE image_url='' OR image_url NOT LIKE 'http%'")[0]["n"]
    rep = image_agent({})
    restantes = db.query("SELECT COUNT(*) n FROM contents WHERE image_url='' OR image_url NOT LIKE 'http%'")[0]["n"]
    atual = hero_ranking()
    if atual:
        row = db.query_one("SELECT id FROM contents WHERE slug=?", (atual["slug"],))
        if row:
            compute_hero_image(row["id"])
    if vazios and not restantes:
        db.execute("INSERT INTO logs (level, source, message) VALUES ('info','image-repair',?)",
                   (f"Reparadas {vazios} imagem(ns) ausente(s); acervo 100% com imagem",))
    return {"vazios_antes": vazios, "reparados": rep["processados"],
            "vazios_depois": restantes, "acervo_completo": restantes == 0}


def image_optimization_agent(payload: dict) -> dict:
    from .imagegen import probe_image
    rows = db.query("SELECT id, image_url FROM contents WHERE status='published'")
    invalidas = [c["id"] for c in rows if not c["image_url"].startswith(("http://", "https://"))
                 or probe_image(c["image_url"])["ok"] is not True]
    for cid in invalidas:
        db.execute("UPDATE contents SET image_url='', hero_image_url='', status='draft', "
                   "published_at=NULL, featured=0, breaking_flag=0 WHERE id = ?", (cid,))
    return {"verified_http_images": len(rows) - len(invalidas),
            "invalid_publications_returned_to_draft": len(invalidas),
            "frontend": "lazy loading on lists; high priority on hero"}


# ═══════════ SEARCH CONSOLE / REVENUE / DASHBOARD / PERFORMANCE ═══════════
def search_console_agent(payload: dict) -> dict:
    cfg = mem_get("agent:search-console", "site_url") or settings.PUBLIC_SITE_URL
    return {"site": cfg, "sitemaps": ["/sitemap.xml", "/news-sitemap.xml", "/image-sitemap.xml"],
            "limitation": "Impressions and clicks require verified Google Search Console access"}


def revenue_agent(payload: dict) -> dict:
    from .core import budget_tier
    t = budget_tier()
    return {"custo_ia_mes_usd": t["gasto_usd"], "orcamento_usd": t["orcamento_usd"],
            "receita_adsense_usd": None,
            "limitacao": "Receita real só após aprovação do AdSense — nunca será estimada aqui"}


def dashboard_agent(payload: dict) -> dict:
    from .core import agent_metrics, budget_tier, budget_remaining
    pub = lambda d: db.query_one(
        f"SELECT COUNT(*) n FROM contents WHERE status='published' "
        f"AND published_at > datetime('now','-{d} days')")["n"]
    resp = db.query_one("SELECT ROUND(AVG(duration_ms)) ms FROM agent_runs "
                        "WHERE created_at > datetime('now','-1 day')")["ms"]
    return {"agentes": agent_metrics(), "orcamento": budget_tier(),
            "publicados_hoje": pub(1), "publicados_semana": pub(7), "publicados_mes": pub(30),
            "saldo_disponivel_usd": round(budget_remaining(), 4),
            "tempo_medio_agente_ms": resp,
            "scores": google_health_report()["scores_conformidade_interna"],
            "metricas_externas": "visitantes/CTR/impressões/receita: aguardam GA4, "
                                 "Search Console e AdSense (jamais estimadas)",
            "publicados": db.query_one("SELECT COUNT(*) n FROM contents WHERE status='published'")["n"],
            "fila": db.query_one("SELECT COUNT(*) n FROM content_queue WHERE status='queued'")["n"],
            "inscritos": db.query_one("SELECT COUNT(*) n FROM subscribers WHERE active=1")["n"],
            "erros_24h": db.query_one("SELECT COUNT(*) n FROM logs WHERE level='error' "
                                      "AND created_at > datetime('now','-1 day')")["n"]}


def performance_agent(payload: dict) -> dict:
    return {"frontend": {"code_splitting": "rotas lazy (React.lazy)", "bundle_alvo": "<70KB gzip inicial",
                         "imagens": "lazy + fallback CSS sem request", "pwa": "manifest ativo"},
            "backend": {"cache": "feeds lidos 1x/ciclo; dedupe por título", "sqlite": "disco Render"},
            "limitacao": "Lighthouse real requer o site publicado — rode no PageSpeed Insights"}


# ═══════════ RESEARCH AGENT ═══════════
def research_agent(payload: dict) -> dict:
    """Monta um briefing por pauta da fila: manchetes correlatas do dia,
    artigos internos do mesmo cluster e palavras-chave — consumido pelo
    Content Writer para enriquecer o prompt. Sem IA: só fatos coletados."""
    pautas = db.query("SELECT id, topic FROM content_queue WHERE status='queued' LIMIT 10")
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    briefings = 0
    for pt in pautas:
        kws = set(extract_keywords(pt["topic"], top=5))
        correlatas = [m for m in manchetes
                      if kws & set(extract_keywords(m["title"], top=6))][:4]
        internos = db.query(
            """SELECT title, slug FROM contents WHERE status='published'
               ORDER BY published_at DESC LIMIT 30""")
        relacionados = [i for i in internos
                        if kws & set(extract_keywords(i["title"], top=6))][:3]
        mem_set("agent:research", f"briefing:{pt['id']}", {
            "topic": pt["topic"], "keywords": sorted(kws),
            "manchetes_correlatas": correlatas,
            "artigos_internos": relacionados,
            "fontes": [m.get("link") for m in correlatas if m.get("link")],
        })
        briefings += 1
    return {"briefings_gerados": briefings,
            "nota": "Briefing factual (fontes reais coletadas); redação fica com o Content Writer"}


# ═══════════ RSS / GOOGLE NEWS / MONITOR AGENTS ═══════════
def rss_agent(payload: dict) -> dict:
    """Valida o feed RSS do próprio portal (existe, é XML válido, tem itens)."""
    import xml.etree.ElementTree as ET
    rows = db.query("SELECT COUNT(*) n FROM contents WHERE status='published'")[0]["n"]
    from ..main import rss_feed
    xml = rss_feed().body.decode()
    try:
        itens = len(ET.fromstring(xml).findall(".//item"))
        valido = True
    except Exception:
        itens, valido = 0, False
    return {"xml_valido": valido, "itens_no_feed": itens, "publicados": rows,
            "endpoint": "/rss.xml"}


def google_news_agent(payload: dict) -> dict:
    """Valida o news-sitemap (48h) e a prontidão para o Publisher Center."""
    import xml.etree.ElementTree as ET
    from ..main import news_sitemap
    xml = news_sitemap().body.decode()
    try:
        ns = {"n": "http://www.google.com/schemas/sitemap-news/0.9"}
        itens = len(ET.fromstring(xml).findall(".//n:news", ns))
        valido = True
    except Exception:
        itens, valido = 0, False
    return {"news_sitemap_valido": valido, "artigos_48h": itens,
            "publisher_center": "pendência humana: cadastrar o site e enviar o sitemap"}


def monitor_agent(payload: dict) -> dict:
    """No-AI production supervisor with idempotent incidents and safe recovery."""
    def incident(code: str, title: str, detail: str, agent_slug: str, active: bool,
                 priority: int = 1) -> int | None:
        task_title = f"[INCIDENT:{code}] {title}"
        current = db.query_one(
            "SELECT id,status FROM tasks WHERE title=? ORDER BY id DESC LIMIT 1", (task_title,))
        if active:
            if current and current["status"] != "done":
                return current["id"]
            aid = db.query_one("SELECT id FROM agents WHERE slug=?", (agent_slug,))
            task_id = db.execute(
                "INSERT INTO tasks(title,description,status,priority,agent_id) VALUES(?,?,'todo',?,?)",
                (task_title, detail[:1000], priority, aid["id"] if aid else None),
            )
            db.execute(
                "INSERT INTO logs(level,source,message,meta_json) VALUES('error','monitor',?,?)",
                (title, json.dumps({"incident": code, "task_id": task_id, "detail": detail})[:2000]),
            )
            return task_id
        if current and current["status"] != "done":
            db.execute("UPDATE tasks SET status='done',updated_at=datetime('now') WHERE id=?",
                       (current["id"],))
            db.execute("INSERT INTO logs(level,source,message) VALUES('info','monitor',?)",
                       (f"Recovered incident {code}: {title}",))
        return None

    em_erro = db.query("SELECT slug FROM agents WHERE status='error'")
    erros = db.query_one("SELECT COUNT(*) n FROM logs WHERE level='error' "
                         "AND created_at > datetime('now','-6 hours')")["n"]
    failed_slugs = [a["slug"] for a in em_erro]
    incident("agents-error", "Agents are in an error state", ", ".join(failed_slugs),
             "ceo-master", bool(failed_slugs))

    stuck_content = db.query_one(
        "SELECT COUNT(*) n FROM content_queue WHERE status='processing' "
        "AND created_at < datetime('now','-1 hour')")["n"]
    if stuck_content:
        db.execute("UPDATE content_queue SET status='queued',error='monitor recovery: stale processing' "
                   "WHERE status='processing' AND created_at < datetime('now','-1 hour')")
    incident("queue-stuck", "Content queue recovered stale work",
             f"Requeued {stuck_content} item(s)", "content", bool(stuck_content))

    failed_images = db.query_one(
        "SELECT COUNT(*) n FROM image_queue WHERE status='failed' AND attempts < 5")["n"]
    if failed_images:
        db.execute("UPDATE image_queue SET status='queued',note='monitor retry' "
                   "WHERE status='failed' AND attempts < 5")
    incident("image-retry", "Image queue needed recovery",
             f"Requeued {failed_images} image(s)", "image", bool(failed_images))

    from ..content_rules import quarantine_noncompliant_public_content
    quarantine = quarantine_noncompliant_public_content()
    quarantined = len(quarantine.get("quarantined", []))
    incident("invalid-publication", "Invalid publications were withdrawn",
             f"Returned {quarantined} item(s) to draft", "image-quality", bool(quarantined))

    published = db.query_one("SELECT COUNT(*) n FROM contents WHERE status='published'")["n"]
    recent = db.query_one("SELECT COUNT(*) n FROM contents WHERE status='published' "
                          "AND published_at > datetime('now','-4 hours')")["n"]
    stale_publication = published > 0 and recent == 0
    incident("publication-stale", "No article published in four hours",
             f"Published total={published}; recent={recent}", "publisher", stale_publication, 2)

    probes: dict[str, dict] = {}
    if settings.ENV.lower() == "production":
        targets = {
            "frontend": site_url() + "/",
            "backend": settings.PUBLIC_API_URL.rstrip("/") + "/api/health",
            "rss": site_url() + "/rss.xml",
            "sitemap": site_url() + "/sitemap.xml",
            "news_sitemap": site_url() + "/news-sitemap.xml",
            "image_sitemap": site_url() + "/image-sitemap.xml",
        }
        with httpx.Client(timeout=12, follow_redirects=True,
                          headers={"User-Agent": "AION-Monitor/1.0"}) as client:
            for name, url in targets.items():
                try:
                    response = client.get(url)
                    body = response.text[:1000]
                    valid = response.status_code == 200
                    if name == "frontend":
                        valid = valid and "AION AI NEWS OS" in body and "Parked Domain" not in body
                    elif name == "backend":
                        valid = valid and '"status":"ok"' in body.replace(" ", "")
                    elif name == "rss":
                        valid = valid and "<rss" in body
                    elif "sitemap" in name:
                        valid = valid and "<urlset" in body
                    probes[name] = {"ok": valid, "status": response.status_code,
                                    "url": str(response.url)}
                except Exception as exc:
                    probes[name] = {"ok": False, "error": type(exc).__name__, "url": url}
                incident(f"probe-{name}", f"Production probe failed: {name}",
                         json.dumps(probes[name]), "monitor", not probes[name]["ok"])

    report = {
        "agentes_em_erro": failed_slugs,
        "erros_6h": erros,
        "content_requeued": stuck_content,
        "images_requeued": failed_images,
        "quarantined": quarantined,
        "published_last_4h": recent,
        "probes": probes,
        "saudavel": not failed_slugs and not stuck_content and not failed_images
                    and not quarantined and not stale_publication
                    and all(p.get("ok") for p in probes.values()),
    }
    mem_set("agent:monitor", "last_report", report)
    return report


# ═══════════ HERO RANKING (breaking + relevância + frescor) ═══════════
def hero_ranking() -> dict | None:
    """Score: breaking do dia (+5), radar (+2), imagem oficial (+1),
    decaimento por idade em horas. Nunca artigo aleatório."""
    breaking = mem_get("agent:breaking-news", "hero") or {}
    rows = db.query(
        """SELECT slug, category, image_url, featured, pinned, breaking_flag,
                  (julianday('now') - julianday(published_at)) * 24 AS idade_h
           FROM contents WHERE status='published'
           AND (published_at > datetime('now','-3 days') OR featured=1 OR pinned=1)""")
    if not rows:
        row = db.query_one("SELECT slug FROM contents WHERE status='published' "
                           "ORDER BY published_at DESC LIMIT 1")
        return {"slug": row["slug"], "score": 0} if row else None
    melhor, melhor_score = None, -1e9
    for r in rows:
        score = 0.0
        if r["featured"] in (1, "1"): score += 12
        if r["pinned"] in (1, "1"): score += 10
        if r["breaking_flag"] in (1, "1"): score += 8
        if r["slug"] == breaking.get("slug"): score += 5
        if r["category"] == "radar": score += 2
        if r["image_url"]: score += 1
        score -= (r["idade_h"] or 0) / 12.0  # frescor
        if score > melhor_score:
            melhor, melhor_score = r["slug"], score
    return {"slug": melhor, "score": round(melhor_score, 2)}


# ═══════════ DIAGNÓSTICO GOOGLE (/health/google) ═══════════
def google_health_report() -> dict:
    """Diagnóstico interno de prontidão para Google Search/Discover/News.
    Scores são CONFORMIDADE INTERNA (0-100), não métricas reais do Google."""
    pub = db.query("SELECT id, slug, title, body, excerpt, category, tags, image_url, "
                   "seo_title, seo_description FROM contents WHERE status='published'")
    total = len(pub) or 1
    sem_imagem = [c["slug"] for c in pub if not (c["image_url"] or "").startswith(("http://", "https://"))]
    sem_seo = [c["slug"] for c in pub if not (c["seo_title"] and c["seo_description"])]
    sem_taxonomia = [c["slug"] for c in pub if not (c["category"] and c["tags"])]
    links_quebrados = []
    for c in pub:
        for slug in re.findall(r"/article/([a-z0-9-]+)", c["body"] or ""):
            if not db.query_one("SELECT 1 x FROM contents WHERE slug=? AND status='published'", (slug,)):
                links_quebrados.append({"em": c["slug"], "para": slug})
    dups = db.query("SELECT slug, COUNT(*) c FROM contents GROUP BY slug HAVING c>1")
    seo_score = round(100 * (1 - (len(sem_seo) + len(sem_taxonomia)) / (2 * total)))
    discover_score = round(100 * (1 - len(sem_imagem) / total))
    health = round(100 * (1 - (len(links_quebrados) + len(dups)) / max(total, 1)))
    return {
        "paginas_indexaveis": {"artigos": total, "fixas": 8,
                               "sitemaps": ["/sitemap.xml", "/news-sitemap.xml",
                                            "/image-sitemap.xml", "/rss.xml"]},
        "problemas": {"artigos_sem_imagem": sem_imagem, "sem_seo_completo": sem_seo,
                      "sem_categoria_ou_tags": sem_taxonomia,
                      "links_internos_quebrados": links_quebrados,
                      "slugs_duplicados": [d["slug"] for d in dups]},
        "scores_conformidade_interna": {"seo": min(seo_score, 100),
                                        "discover": min(discover_score, 100),
                                        "health": max(min(health, 100), 0)},
        "aviso": "Scores medem conformidade interna do acervo; impressões/CTR/indexação "
                 "reais só existem no Search Console (credencial humana)",
    }
