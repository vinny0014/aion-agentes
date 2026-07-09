"""Arquitetura de Agentes AION.

Cada agente tem responsabilidade única. Nesta fase, os agentes são registrados
no banco e o pipeline de conteúdo roda sem provedores externos (fila fica em
'blocked' com pendência humana registrada até que uma API key seja configurada).
Quando as chaves forem adicionadas ao .env, `providers.generate()` passa a
gerar conteúdo real sem mudanças de arquitetura.
"""
import json

from ..core import database as db
from ..core.config import settings

AGENT_DEFINITIONS = [
    ("ceo-master", "CEO MASTER", "orquestracao",
     "Coordena todos os agentes, define prioridades e aprova entregas."),
    ("developer", "Developer", "engenharia",
     "Implementa funcionalidades, corrige bugs e mantém a base de código."),
    ("qa", "QA", "qualidade",
     "Executa testes, valida fluxos críticos e bloqueia regressões."),
    ("content", "Content", "conteudo",
     "Produz e revisa o conteúdo diário do portal a partir da fila."),
    ("seo", "SEO", "seo",
     "Otimiza títulos, meta descriptions, slugs, schema e sitemap."),
    ("github", "GitHub", "versionamento",
     "Organiza commits, branches, PRs e documentação do repositório."),
    ("deploy", "Deploy", "devops",
     "Prepara e executa deploys no Vercel (frontend) e Render (backend)."),
    ("monitor", "Monitor", "observabilidade",
     "Acompanha health check, logs e alertas de erro."),
    ("cost-guard", "Cost Guard", "custos",
     "Monitora consumo de APIs de IA e impede estouro de orçamento."),
    ("discovery", "Discovery Agent", "pesquisa",
     "Varre fontes oficiais (RSS de OpenAI, Google, Anthropic, HF, arXiv...) e enfileira pautas."),
    ("fact-check", "Fact Check Agent", "verificacao",
     "Verifica placeholders, duplicidade, links internos e bloqueia publicação com problemas."),
    ("image", "Image Agent", "imagens",
     "Garante imagem em todo artigo: oficial (com metadados) ou arte editorial 1200x630."),
    ("image-quality", "Image Quality Check", "qualidade-imagens",
     "Bloqueia vazio/invalido e re-enfileira capas genericas para virar foto."),
    ("image-repair", "Image Repair Agent", "reparo-imagens",
     "Varre o acervo e completa qualquer image_url vazio, sem duplicar."),
    ("image-prompt", "Image Prompt Agent", "imagens",
     "Cria prompts de imagens originais por artigo, sem marcas nem material protegido."),
    ("translation", "Translation Agent", "idiomas",
     "Prepara versões EN/ES; fila registrada até haver provedor de IA."),
    ("social-media", "Social Media Agent", "distribuicao",
     "Gera posts com texto, hashtags e CTA para X, LinkedIn, IG, Threads, Bluesky e Mastodon."),
    ("newsletter", "Newsletter Agent", "email",
     "Segmenta inscritos e prepara edições; envio real aguarda provedor de e-mail."),
    ("analytics", "Analytics Agent", "metricas",
     "Métricas internas reais e recomendações; GA4/Cloudflare quando conectados."),
    ("adsense-opt", "AdSense Optimization Agent", "monetizacao",
     "Audita conformidade e posições de anúncio; nunca aplica práticas proibidas."),
    ("security", "Security Agent", "seguranca",
     "Audita rate limit, headers, SQLi, XSS, CSRF, segredos e senhas."),
    ("research", "Research Agent", "pesquisa-profunda",
     "Monta briefing factual por pauta: manchetes correlatas, fontes e links internos."),
    ("breaking-news", "Breaking News Agent", "urgencia",
     "Detecta a manchete mais quente e troca o hero automaticamente."),
    ("trend-hunter", "Trend Hunter Agent", "tendencias",
     "Extrai tendências das manchetes e cria pautas de guias."),
    ("google-discover", "Google Discover Agent", "discover",
     "Audita requisitos do Discover: imagens grandes, títulos, news sitemap."),
    ("image-optimization", "Image Optimization Agent", "imagens",
     "Valida URLs de imagens oficiais e garante fallback editorial."),
    ("search-console", "Search Console Agent", "indexacao",
     "Gerencia sitemaps e prepara integração com o Search Console."),
    ("revenue", "Revenue Agent", "receita",
     "Consolida custo de IA vs receita AdSense (real, nunca estimada)."),
    ("dashboard", "Dashboard Agent", "executivo",
     "Consolida o painel executivo: agentes, orçamento, conteúdo, erros."),
    ("performance", "Performance Agent", "performance",
     "Audita code splitting, cache, imagens e metas de Core Web Vitals."),
    ("publisher", "Publisher Agent", "publicacao",
     "Publica o Radar IA diário (curadoria original com atribuição) e artigos aprovados."),
    ("rss", "RSS Agent", "feeds",
     "Valida e mantém o feed RSS 2.0 do portal."),
    ("google-news", "Google News Agent", "google-news",
     "Valida o news-sitemap e a prontidão para o Publisher Center."),
    ("scheduler", "Scheduler Agent", "automacao",
     "Agenda pipelines, evita concorrência e impede loops."),
    ("discovery-growth", "Discovery Growth Agent", "crescimento",
     "Maximiza alcance orgânico: calendário editorial, tendências, palavras-chave, "
     "clusters de conteúdo e preparação para Google Discover/Search Console/Analytics/"
     "AdSense/Trends, Bing Webmaster e Cloudflare Analytics."),
]


def seed_agents() -> None:
    """Registra os agentes padrão (idempotente)."""
    for slug, name, role, desc in AGENT_DEFINITIONS:
        if not db.query_one("SELECT id FROM agents WHERE slug = ?", (slug,)):
            db.execute(
                "INSERT INTO agents (slug, name, role, description) VALUES (?,?,?,?)",
                (slug, name, role, desc),
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
        "Nenhuma API de IA configurada. Adicione OPENAI_API_KEY, ANTHROPIC_API_KEY, "
        "OPENROUTER_API_KEY ou GEMINI_API_KEY ao arquivo .env do backend."
    )


TEMPLATES = {
    "artigo_padrao": (
        "Write an ORIGINAL article in English (US) para o portal AION sobre: {topic}. "
        "Between 800 and 1500 words. Required markdown structure: "
        "a 2-sentence lead; ## subheadings for 3-4 body sections; "
        "## FAQ with 3 questions and answers; ## Conclusion with a reading CTA. "
        "Cite sources with markdown links when provided in context. "
        "Never copy third-party text; never use lorem ipsum or placeholders."
    ),
    "noticia_curta": (
        "Escreva uma notícia curta (até 300 palavras) sobre: {topic}. "
        "Lead direto, contexto e fecho."
    ),
    "comparativo": (
        "Write an original COMPARISON article in English (US) (800-1500 palavras) sobre: {topic}. "
        "Estrutura markdown: lead; ## critérios de comparação; ## análise de cada opção; "
        "## tabela-resumo em texto; ## FAQ (3 perguntas); ## Conclusão com recomendação e CTA. "
        "Nunca invente números; cite fontes fornecidas no contexto."
    ),
    "evergreen": (
        "Write a timeless EVERGREEN article in English (US) (800-1500 palavras) sobre: {topic}. "
        "Estrutura: lead; ## conceitos fundamentais; ## como funciona; ## aplicações; "
        "## FAQ (3 perguntas); ## Conclusão com CTA. Didático, sem referências datadas."
    ),
    "guia_pratico": (
        "Escreva um guia prático passo a passo sobre: {topic}, com pré-requisitos e dicas."
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
                status: str = "draft") -> int:
    from .core import mem_get as _mg
    brief = _mg("agent:research", f"briefing:{item['id']}") or {}
    tags = ",".join((brief.get("keywords") or ["ia"])[:5])
    categoria = _TEMPLATE_CATEGORIA.get(item.get("template", ""), "news")
    cid = db.execute(
        """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
           seo_title, seo_description, category, tags)
           VALUES (?,?,?,?,?,
                   (SELECT id FROM agents WHERE slug = 'content'), ?, ?, ?, ?)""",
        (title, _unique_slug(slug), body, excerpt, status, title, excerpt[:160],
         categoria, tags),
    )
    db.execute(
        "UPDATE content_queue SET status = 'done', result_content_id = ? WHERE id = ?",
        (cid, item["id"]),
    )
    return cid


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
    items = db.query("SELECT * FROM content_queue WHERE status = 'queued' ORDER BY id LIMIT ?", (max(limite, 10),))
    processed, offline, failed = 0, 0, 0
    for item in items:
        template = item["template"] if item["template"] in TEMPLATES else "artigo_padrao"
        try:
            provider = resolve_provider(item["provider"])
            prompt = TEMPLATES[template].format(topic=item["topic"])
            from .core import mem_get as _mg
            brief = _mg("agent:research", f"briefing:{item['id']}")
            if brief:
                fontes = "; ".join(brief.get("fontes", [])[:4])
                prompt += (f"\nContexto factual (cite as fontes): "
                           f"manchetes correlatas: "
                           f"{'; '.join(m['title'] for m in brief.get('manchetes_correlatas', []))}. "
                           f"Fontes: {fontes}. "
                           f"Linke internamente: "
                           f"{'; '.join('/conteudo/'+a['slug'] for a in brief.get('artigos_internos', []))}.")
            db.execute(
                "UPDATE content_queue SET status = 'processing', provider = ? WHERE id = ?",
                (provider, item["id"]),
            )
            if limite <= 0:
                continue  # IA suspensa pelo Cost Guard; item permanece na fila
            limite -= 1
            try:
                prov.LAST_USAGE["tokens"] = 0
                body = prov.generate(provider, prompt)
                preco = db.query_one(
                    "SELECT value FROM app_settings WHERE key='preco_por_1k_tokens_usd'")
                custo = (prov.LAST_USAGE["tokens"] / 1000.0) * (
                    float(preco["value"]) if preco else 0.0006)
                record_cost("content", prov.LAST_USAGE["tokens"], custo)
                title = item["topic"].strip().capitalize()
                _save_draft(item, title, prov.slugify(item["topic"]), body,
                            f"Artigo sobre {item['topic']} gerado via {provider}.")
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
    return {"processed": processed, "offline_drafts": offline, "failed": failed,
            "scanned": len(items)}
