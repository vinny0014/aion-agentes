"""AION agent registry and pluggable content pipeline.

Without an external AI provider, the queue produces structured offline drafts
and records the missing credential. Every draft still needs fact checking, an
English-language gate and a persisted raster image before publication.
"""
import json

from ..core import database as db
from ..core.config import settings

AGENT_DEFINITIONS = [
    ("ceo-master", "CEO MASTER", "orchestration",
     "Coordinates agents, prioritizes work and approves deliverables."),
    ("developer", "Developer", "engineering",
     "Implements features, fixes bugs and maintains the codebase."),
    ("qa", "QA", "quality",
     "Runs tests, validates critical flows and blocks regressions."),
    ("content", "Content", "content",
     "Produces and reviews the newsroom's daily content queue."),
    ("seo", "SEO", "seo",
     "Optimizes titles, descriptions, slugs, structured data and sitemaps."),
    ("github", "GitHub", "version-control",
     "Organizes commits, branches, pull requests and repository documentation."),
    ("deploy", "Deploy", "devops",
     "Prepares deployments to Vercel and Render."),
    ("monitor", "Monitor", "observability",
     "Monitors health checks, logs and error alerts."),
    ("cost-guard", "Cost Guard", "cost-control",
     "Monitors AI API spend and enforces the budget."),
    ("discovery", "Discovery Agent", "research",
     "Scans reputable AI RSS sources and queues story ideas."),
    ("fact-check", "Fact Check Agent", "verification",
     "Checks placeholders, duplicates, internal links, language and publication images."),
    ("image", "Image Agent", "images",
     "Validates and persists a real 1200x630 raster image before publication."),
    ("image-quality", "Image Quality Check", "image-quality",
     "Blocks invalid images and requeues content for a verified raster asset."),
    ("image-repair", "Image Repair Agent", "image-repair",
     "Scans the archive and repairs missing images without duplication."),
    ("image-prompt", "Image Prompt Agent", "images",
     "Creates original editorial image prompts without brands or protected material."),
    ("translation", "Public Language Agent", "languages",
     "Audits and enforces English as the only public language."),
    ("social-media", "Social Media Agent", "distribution",
     "Drafts attributed social posts for supported networks."),
    ("newsletter", "Newsletter Agent", "email",
     "Segments subscribers and prepares editions; delivery requires an email provider."),
    ("analytics", "Analytics Agent", "metrics",
     "Reports real internal metrics and uses external analytics only when connected."),
    ("adsense-opt", "AdSense Optimization Agent", "monetization",
     "Audits advertising compliance and placements."),
    ("security", "Security Agent", "security",
     "Audits rate limits, headers, injection, XSS, secrets and passwords."),
    ("research", "Research Agent", "deep-research",
     "Builds factual briefs with related headlines, sources and internal links."),
    ("breaking-news", "Breaking News Agent", "breaking-news",
     "Detects urgent headlines and updates the homepage hero."),
    ("trend-hunter", "Trend Hunter Agent", "trends",
     "Extracts trends from headlines and creates English story ideas."),
    ("google-discover", "Google Discover Agent", "discover",
     "Audits Discover requirements including large images, titles and news sitemap."),
    ("image-optimization", "Image Optimization Agent", "images",
     "Returns publications with invalid images to draft."),
    ("search-console", "Search Console Agent", "indexing",
     "Audits sitemaps and Search Console readiness."),
    ("revenue", "Revenue Agent", "revenue",
     "Compares real AI spend with real advertising revenue."),
    ("dashboard", "Dashboard Agent", "executive",
     "Consolidates agents, budget, content and errors for the dashboard."),
    ("performance", "Performance Agent", "performance",
     "Audits code splitting, cache, images and Core Web Vitals readiness."),
    ("publisher", "Publisher Agent", "publishing",
     "Publishes attributed AI Radar editions and approved articles."),
    ("rss", "RSS Agent", "feeds",
     "Validates the newsroom's RSS 2.0 feed."),
    ("google-news", "Google News Agent", "google-news",
     "Validates the news sitemap and Publisher Center readiness."),
    ("scheduler", "Scheduler Agent", "automation",
     "Schedules pipelines, prevents concurrency and stops runaway loops."),
    ("discovery-growth", "Discovery Growth Agent", "growth",
     "Improves organic reach through editorial planning, trends, keywords, "
     "content clusters and preparation for Google Discover/Search Console/Analytics/"
     "AdSense/Trends, Bing Webmaster and Cloudflare Analytics."),
]

PRIMARY_AGENTS = {
    "ceo-master", "discovery", "content", "fact-check", "image",
    "image-quality", "seo", "monitor", "cost-guard",
}
PARTIAL_AGENTS = {
    "social-media", "newsletter", "analytics", "adsense-opt", "google-discover",
    "search-console", "revenue",
}
BLOCKED_EXTERNAL_AGENTS = {"github", "deploy"}
AGENT_HANDLERS = {
    "ceo-master": "orchestrator.run_cycle",
    "discovery": "team.discovery_agent",
    "research": "team.research_agent",
    "trend-hunter": "team.trend_hunter_agent",
    "breaking-news": "team.breaking_news_agent",
    "content": "team.content_writer_agent",
    "seo": "team.seo_agent",
    "image": "team.image_agent",
    "image-prompt": "team.image_prompt_agent",
    "image-repair": "team.image_repair_agent",
    "image-optimization": "team.image_optimization_agent",
    "image-quality": "team.image_quality_agent",
    "fact-check": "team.fact_check_agent",
    "publisher": "team.publisher_agent",
    "dashboard": "team.dashboard_agent",
    "google-discover": "team.google_discover_agent",
    "google-news": "team.google_news_agent",
    "rss": "team.rss_agent",
    "newsletter": "team.newsletter_agent",
    "social-media": "team.social_media_agent",
    "translation": "team.translation_agent",
    "analytics": "team.analytics_agent",
    "discovery-growth": "team.discovery_growth_agent",
    "search-console": "team.search_console_agent",
    "adsense-opt": "team.adsense_agent",
    "revenue": "team.revenue_agent",
    "cost-guard": "team.cost_guard_agent",
    "performance": "team.performance_agent",
    "qa": "team.qa_agent",
    "security": "team.security_agent",
    "monitor": "team.monitor_agent",
    "scheduler": "app.lifespan.APScheduler",
}


def agent_classification(slug: str) -> str:
    if slug in PRIMARY_AGENTS:
        return "OPERATIONAL"
    if slug in PARTIAL_AGENTS:
        return "PARTIAL"
    if slug in BLOCKED_EXTERNAL_AGENTS:
        return "BLOCKED_EXTERNAL"
    return "INTERNAL_MODULE"


def agent_runtime_config(slug: str) -> dict:
    classification = agent_classification(slug)
    handler = AGENT_HANDLERS.get(slug)
    return {
        "classification": classification,
        "entrypoint": "run_agent" if handler and slug not in {"ceo-master", "scheduler"} else handler,
        "handler": handler,
        "input": "JSON task payload",
        "execution": ("orchestrator pipeline" if handler else
                      "external connector" if slug in BLOCKED_EXTERNAL_AGENTS else
                      "registered capability without an executable handler"),
        "output": "structured JSON",
        "log": "agent_runs + logs",
        "database": "SQLite persistent disk",
        "handoff": "memory + pipeline result",
        "cost": "recorded in agent_runs",
    }


def seed_agents() -> None:
    """Registra os agentes padrão (idempotente)."""
    for slug, name, role, desc in AGENT_DEFINITIONS:
        config = json.dumps(agent_runtime_config(slug), separators=(",", ":"))
        db.execute(
            """INSERT INTO agents (slug, name, role, description, config_json) VALUES (?,?,?,?,?)
               ON CONFLICT(slug) DO UPDATE SET name=excluded.name, role=excluded.role,
               description=excluded.description, config_json=excluded.config_json""",
            (slug, name, role, desc, config),
        )


# ---------------- Provedores de IA (plugáveis) ----------------
class ProviderNotConfigured(Exception):
    pass


def resolve_provider(requested: str) -> str:
    """Escolhe o provedor disponível; lança erro se nenhum estiver configurado."""
    keys = {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "openrouter": settings.OPENROUTER_API_KEY,
        "gemini": settings.GEMINI_API_KEY,
    }
    if requested != "pending" and keys.get(requested):
        return requested
    for name, key in keys.items():
        if key:
            return name
    raise ProviderNotConfigured(
        "No AI provider is configured. Add OPENAI_API_KEY, ANTHROPIC_API_KEY, "
        "OPENROUTER_API_KEY or GEMINI_API_KEY to the backend environment."
    )


TEMPLATES = {
    "artigo_padrao": (
        "Write an original article in US English for AION about: {topic}. "
        "Between 800 and 1500 words. Required markdown structure: "
        "a 2-sentence lead; ## subheadings for 3-4 body sections; "
        "## FAQ with 3 questions and answers; ## Conclusion with a reading CTA. "
        "Cite sources with markdown links when provided in context. "
        "Never copy third-party text; never use lorem ipsum or placeholders."
    ),
    "noticia_curta": (
        "Write an original short news report in US English (up to 300 words) about: {topic}. "
        "Use a direct lead, factual context, source links and a concise ending."
    ),
    "comparativo": (
        "Write an original comparison article in US English (800-1500 words) about: {topic}. "
        "Markdown structure: lead; ## comparison criteria; ## analysis of each option; "
        "## summary table in text; ## FAQ (3 questions); ## Conclusion with recommendation and CTA. "
        "Never invent numbers; cite every source supplied in context."
    ),
    "evergreen": (
        "Write a timeless evergreen article in US English (800-1500 words) about: {topic}. "
        "Structure: lead; ## fundamentals; ## how it works; ## applications; "
        "## FAQ (3 questions); ## Conclusion with CTA. Be educational and avoid dated claims."
    ),
    "guia_pratico": (
        "Write a practical step-by-step guide in US English about: {topic}, with prerequisites, safety notes and tips."
    ),
}


def _unique_slug(base: str) -> str:
    slug, n = base, 2
    while db.query_one("SELECT id FROM contents WHERE slug = ?", (slug,)):
        slug = f"{base}-{n}"
        n += 1
    return slug


_TEMPLATE_CATEGORIA = {"noticia_curta": "news", "artigo_padrao": "news",
                        "guia_pratico": "guides", "comparativo": "comparisons",
                        "evergreen": "fundamentals"}


def _save_draft(item: dict, title: str, slug: str, body: str, excerpt: str,
                status: str = "draft", metadata: dict | None = None) -> int:
    from .core import mem_get as _mg
    brief = _mg("agent:research", f"briefing:{item['id']}") or {}
    metadata = metadata or {}
    tags_value = metadata.get("tags") or brief.get("keywords") or ["ai"]
    if isinstance(tags_value, str):
        tags_value = [part.strip() for part in tags_value.split(",")]
    tags = ",".join(str(tag).strip().lower() for tag in tags_value[:5] if str(tag).strip())
    categoria = str(metadata.get("category") or
                    _TEMPLATE_CATEGORIA.get(item.get("template", ""), "news")).strip().lower()
    seo_title = str(metadata.get("seo_title") or title)[:60]
    seo_description = str(metadata.get("meta_description") or excerpt)[:160]
    source_url = next((url for url in brief.get("fontes", []) if url), "")
    cid = db.execute(
        """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
           seo_title, seo_description, category, tags, source_url)
           VALUES (?,?,?,?,?,
                   (SELECT id FROM agents WHERE slug = 'content'), ?, ?, ?, ?, ?)""",
        (title, _unique_slug(slug), body, excerpt, status, seo_title, seo_description,
         categoria, tags, source_url),
    )
    if metadata.get("social_text"):
        from .core import mem_set as _ms
        _ms("agent:social-media", f"draft:{cid}", str(metadata["social_text"])[:600])
    db.execute(
        "UPDATE content_queue SET status = 'done', result_content_id = ? WHERE id = ?",
        (cid, item["id"]),
    )
    return cid


def _parse_generated_article(raw: str, topic: str, template: str) -> dict:
    """Parse the single provider response; retain a safe draft if JSON is malformed."""
    candidate = (raw or "").strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(candidate)
    except Exception:
        match = __import__("re").search(r"\{.*\}", candidate, __import__("re").S)
        try:
            data = json.loads(match.group(0)) if match else {}
        except Exception:
            data = {}
    if not isinstance(data, dict) or len(str(data.get("body") or "")) < 200:
        body = raw.strip()
        first = next((line.strip("# ") for line in body.splitlines() if len(line.strip()) > 40), topic)
        return {
            "title": topic.strip(), "excerpt": first[:160], "body": body,
            "category": _TEMPLATE_CATEGORIA.get(template, "news"), "tags": ["ai"],
            "seo_title": topic.strip()[:60], "meta_description": first[:160],
        }
    data["title"] = str(data.get("title") or topic).strip()[:200]
    data["excerpt"] = str(data.get("excerpt") or data["body"][:160]).strip()[:240]
    data["body"] = str(data["body"]).strip()
    return data


def process_queue_once() -> dict:
    """Processa a fila de conteúdo.

    - Com provedor de IA configurado: gera o artigo completo (rascunho para revisão).
    - Sem provedor: gera rascunho estruturado offline — a produção diária nunca para —
      e registra a pendência humana (configurar API key) uma única vez em log.
    """
    from . import providers as prov
    from .core import budget_tier, record_cost

    tier = budget_tier()
    limite = {"normal": 10, "alerta": 10, "economico": 5,
              "reducao": 2, "apenas-principais": 1, "suspenso": 0}[tier["modo"]]
    if limite <= 0:
        waiting = db.query_one("SELECT COUNT(*) AS n FROM content_queue WHERE status='queued'")["n"]
        return {"processed": 0, "offline_drafts": 0, "failed": 0, "scanned": 0,
                "waiting_for_budget": waiting}
    items = db.query("SELECT * FROM content_queue WHERE status = 'queued' ORDER BY id LIMIT ?", (limite,))
    processed, offline, failed = 0, 0, 0
    for item in items:
        template = item["template"] if item["template"] in TEMPLATES else "artigo_padrao"
        try:
            provider = resolve_provider(item["provider"])
            prompt = TEMPLATES[template].format(topic=item["topic"])
            prompt += (
                "\nReturn only one valid JSON object with these keys: title, excerpt, body, "
                "category, tags (array), seo_title, meta_description, social_text. "
                "The body must be Markdown. Preserve official capitalization of product, company "
                "and person names. Do not add facts that are absent from the supplied sources."
            )
            from .core import mem_get as _mg
            brief = _mg("agent:research", f"briefing:{item['id']}")
            if brief:
                fontes = "; ".join(brief.get("fontes", [])[:4])
                prompt += (f"\nFactual context (cite these sources): "
                           f"related headlines: "
                           f"{'; '.join(m['title'] for m in brief.get('manchetes_correlatas', []))}. "
                           f"Sources: {fontes}. "
                           f"Add relevant internal links: "
                           f"{'; '.join('/article/'+a['slug'] for a in brief.get('artigos_internos', []))}.")
            db.execute(
                "UPDATE content_queue SET status = 'processing', provider = ? WHERE id = ?",
                (provider, item["id"]),
            )
            limite -= 1
            try:
                prov.LAST_USAGE["tokens"] = 0
                raw = prov.generate(provider, prompt)
                article = _parse_generated_article(raw, item["topic"], template)
                preco = db.query_one(
                    "SELECT value FROM app_settings WHERE key='preco_por_1k_tokens_usd'")
                custo = (prov.LAST_USAGE["tokens"] / 1000.0) * (
                    float(preco["value"]) if preco else 0.0006)
                record_cost("content", prov.LAST_USAGE["tokens"], custo)
                title = article["title"]
                _save_draft(item, title, prov.slugify(title), article["body"],
                            article["excerpt"], metadata=article)
                processed += 1
            except Exception as exc:  # falha de rede/quota — não derruba a fila
                db.execute(
                    "UPDATE content_queue SET status = 'failed', error = ? WHERE id = ?",
                    (f"{type(exc).__name__}: {exc}", item["id"]),
                )
                db.execute(
                    "INSERT INTO logs (level, source, message, meta_json) VALUES ('error','content-pipeline',?,?)",
                    (f"Falha ao gerar conteúdo via {provider}",
                     json.dumps({"queue_id": item["id"], "erro": str(exc)[:300]})),
                )
                failed += 1
        except ProviderNotConfigured as exc:
            draft = prov.offline_draft(item["topic"], template)
            _save_draft(item, draft["title"], draft["slug"], draft["body"], draft["excerpt"])
            db.execute(
                "INSERT INTO logs (level, source, message, meta_json) VALUES ('warn','content-pipeline',?,?)",
                ("Offline draft generated (HUMAN ACTION: configure an AI API key in .env)",
                 json.dumps({"queue_id": item["id"], "topic": item["topic"], "detalhe": str(exc)})),
            )
            offline += 1
    # Due Editorial Studio items are evaluated during the hourly queue cycle too.
    from ..content_rules import publication_issues
    scheduled = db.query("SELECT * FROM contents WHERE status='draft' "
                         "AND scheduled_at != '' AND scheduled_at <= datetime('now')")
    scheduled_published = 0
    for content in scheduled:
        if publication_issues(content):
            continue
        db.execute(
            "UPDATE contents SET status='published', published_at=datetime('now'), scheduled_at='', "
            "hero_image_url=image_url, hero_image_alt=image_alt, hero_image_credit=image_credit, "
            "hero_image_width='1200', hero_image_height='630', hero_image_source='primary' WHERE id=?",
            (content["id"],),
        )
        scheduled_published += 1
    return {"processed": processed, "offline_drafts": offline, "failed": failed,
            "scheduled_published": scheduled_published,
            "scanned": len(items)}
