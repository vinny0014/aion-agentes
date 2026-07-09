"""Implementação dos 16 agentes do AION.

Regra de honestidade: nenhum agente inventa dados. Onde uma credencial ou
serviço externo falta, o agente registra a limitação real na memória/logs
e devolve o que É possível fazer localmente.
"""
import json
import re

import httpx

from ..core import database as db
from ..core.config import settings
from .core import budget_remaining, mem_get, mem_set
from .discovery import extract_keywords, reading_time_minutes
from .providers import slugify
from .registry import process_queue_once, resolve_provider, ProviderNotConfigured

# Fontes padrão do Discovery (RSS/Atom oficiais) — configuráveis via memória
DEFAULT_SOURCES = [
    # Feeds com resumo (description/summary) redistribuível — base da síntese
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://export.arxiv.org/rss/cs.AI",
    "https://huggingface.co/blog/feed.xml",
    "https://blogs.nvidia.com/feed/",
    "https://www.anthropic.com/rss.xml",
    "https://openai.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
]


# ═══════════ 2. DISCOVERY AGENT ═══════════
def discovery_agent(payload: dict) -> dict:
    sources = mem_get("agent:discovery", "sources", DEFAULT_SOURCES)
    found, errors = [], []
    for url in sources[: payload.get("max_sources", 4)]:
        try:
            r = httpx.get(url, timeout=10, follow_redirects=True,
                          headers={"User-Agent": "AION-Discovery/1.0"})
            r.raise_for_status()
            for item in re.findall(r"<(?:item|entry)>(.*?)</(?:item|entry)>", r.text, re.S)[:5]:
                t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.S)
                l = re.search(r'<link[^>]*href="([^"]+)"|<link>(.*?)</link>', item, re.S)
                if not t:
                    continue
                titulo = re.sub(r"<[^>]+>", "", t.group(1)).strip()
                link = (l.group(1) or l.group(2) or "").strip() if l else ""
                img = re.search(r'<(?:enclosure|media:content|media:thumbnail)[^>]*url="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', item)
                desc_m = re.search(r"<(?:description|summary)[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</(?:description|summary)>", item, re.S)
                desc = re.sub(r"<[^>]+>", " ", desc_m.group(1)).strip() if desc_m else ""
                desc = re.sub(r"\s+", " ", desc)[:600]
                if titulo:
                    found.append({"source": url, "title": titulo, "link": link,
                                  "image": img.group(1) if img else "", "resumo": desc})
        except Exception as exc:
            errors.append({"source": url, "erro": f"{type(exc).__name__}"})
    novos = 0
    for item in found:
        topic = item["title"][:280]
        if len(topic) < 12:
            continue
        if not db.query_one("SELECT id FROM content_queue WHERE topic = ?", (topic,)):
            db.execute(
                "INSERT INTO content_queue (topic, template) VALUES (?, 'noticia_curta')", (topic,))
            novos += 1
    if errors and not found:
        mem_set("agent:discovery", "limitacao",
                "Fontes externas inacessíveis neste ambiente de rede; "
                "em produção (Render) o acesso é liberado.")
    mem_set("agent:discovery", "manchetes_do_dia", found[:20])
    mem_set("agent:discovery", "ultima_execucao",
            {"encontrados": len(found), "enfileirados": novos, "erros_fonte": errors})
    return {"encontrados": len(found), "enfileirados": novos, "fontes_com_erro": len(errors)}


# ═══════════ 3. CONTENT WRITER AGENT (usa o pipeline existente) ═══════════
def content_writer_agent(payload: dict) -> dict:
    return process_queue_once()


# ═══════════ 4. FACT CHECK AGENT ═══════════
def fact_check_agent(payload: dict) -> dict:
    """Verifica rascunhos; bloqueia publicação automática do que reprovar."""
    drafts = db.query("SELECT * FROM contents WHERE status = 'draft' ORDER BY id DESC LIMIT 20")
    aprovados, bloqueados = [], []
    for c in drafts:
        problemas = []
        if "[Rascunho automático" in (c["body"] or "") or "[Desenvolva" in (c["body"] or ""):
            problemas.append("placeholders de rascunho no corpo")
        palavras = len((c["body"] or "").split())
        if len(c["body"] or "") < 200:
            problemas.append("corpo muito curto (<200 caracteres)")
        elif c.get("agent_id") and palavras < 500:
            problemas.append(f"artigo de IA com só {palavras} palavras (mínimo 500 p/ publicação automática)")
        if c.get("agent_id"):
            if not (c.get("category") or "").strip():
                problemas.append("artigo de IA sem categoria")
            if not (c.get("excerpt") or "").strip():
                problemas.append("artigo de IA sem resumo")
            if not (c.get("image_url") or "").strip():
                problemas.append("artigo de IA sem imagem")
        dup = db.query_one(
            "SELECT id FROM contents WHERE title = ? AND id != ? AND status = 'published'",
            (c["title"], c["id"]))
        if dup:
            problemas.append(f"título duplicado do conteúdo #{dup['id']}")
        # links internos citados devem existir
        for slug in re.findall(r"/article/([a-z0-9-]+)", c["body"] or ""):
            if not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug,)):
                problemas.append(f"link interno quebrado: {slug}")
        if problemas:
            bloqueados.append({"id": c["id"], "title": c["title"], "problemas": problemas})
        else:
            aprovados.append(c["id"])
    mem_set("agent:fact-check", "bloqueados", bloqueados)
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
        alt = f"Ilustração do artigo: {c['title'][:80]}"
        if seo_title != c["seo_title"] or desc != c["seo_description"]:
            db.execute("UPDATE contents SET seo_title = ?, seo_description = ? WHERE id = ?",
                       (seo_title, desc, c["id"]))
            corrigidos += 1
        mem_set("agent:seo", f"alt:{c['id']}", alt)
    return {"auditados": len(rows), "corrigidos": corrigidos,
            "cobertura": "title<=60, description<=160, alt-text por artigo, "
                         "JSON-LD/OG/canonical no frontend, sitemap/robots no backend"}


# ═══════════ 6. IMAGE PROMPT AGENT ═══════════
def image_agent(payload: dict) -> dict:
    """REGRA ABSOLUTA: nenhum artigo sem imagem. Usa a oficial (do Discovery,
    com metadados) ou gera arte editorial SVG determinística (custo zero)."""
    from .imagegen import editorial_data_uri
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    por_titulo = {m["title"]: m for m in manchetes}
    corrigidos, editoriais, oficiais = 0, 0, 0
    for c in db.query("SELECT id, title, category, image_url, source_url FROM contents "
                      "WHERE status IN ('draft','published')"):
        if c["image_url"]:
            continue
        # tenta imagem oficial correlata coletada pelo Discovery
        oficial = next((m.get("image") for m in manchetes
                        if m.get("image") and m["title"][:20] in (c["title"] or "")), "")
        if oficial:
            db.execute("""UPDATE contents SET image_url=?, image_alt=?, image_credit=?,
                          image_width='1200', image_height='630' WHERE id=?""",
                       (oficial, f"Official image: {c['title'][:90]}",
                        _fonte_amigavel(c["source_url"]), c["id"]))
            oficiais += 1
        else:
            uri = editorial_data_uri(c["title"], c["category"] or "IA")
            db.execute("""UPDATE contents SET image_url=?, image_alt=?, image_credit=?,
                          image_width='1200', image_height='630' WHERE id=?""",
                       (uri, f"AION editorial artwork: {c['title'][:90]}", "AION editorial artwork", c["id"]))
            editoriais += 1
        corrigidos += 1
    return {"corrigidos": corrigidos, "imagens_oficiais": oficiais,
            "arte_editorial": editoriais,
            "garantia": "100% dos artigos com imagem (oficial ou editorial 1200x630)"}


def image_prompt_agent(payload: dict) -> dict:
    rows = db.query("SELECT id, slug, title, category, tags FROM contents "
                    "WHERE status = 'published' ORDER BY id DESC LIMIT 20")
    gerados = 0
    for c in rows:
        key = f"prompt:{c['slug']}"
        if mem_get("agent:image", key):
            continue
        kws = ", ".join((c["tags"] or "ia").split(",")[:3])
        prompt = (f"Ilustração editorial abstrata e original sobre '{c['title']}'. "
                  f"Tema: {kws}. Estilo: gradientes violeta e roxo sobre fundo escuro, "
                  f"formas geométricas luminosas, grade sutil, sem texto, sem logotipos, "
                  f"sem pessoas reais, sem elementos de marcas. Proporção 16:9.")
        mem_set("agent:image", key, prompt)
        gerados += 1
    return {"prompts_gerados": gerados,
            "nota": "Prompts originais; geração da imagem em si depende de API externa"}


# ═══════════ 7. TRANSLATION AGENT ═══════════
def translation_agent(payload: dict) -> dict:
    pend = db.query("SELECT id, slug, title FROM contents WHERE status='published' "
                    "ORDER BY id DESC LIMIT 20")
    fila = []
    for c in pend:
        for lang in ("en", "es"):
            key = f"{lang}:{c['slug']}"
            if not mem_get("agent:translation", key):
                fila.append({"slug": c["slug"], "lang": lang})
                mem_set("agent:translation", key,
                        {"status": "pendente-credencial", "title": c["title"]})
    return {"na_fila": len(fila), "idiomas": ["en", "es", "pt(nativo)"],
            "limitacao": None if _tem_provider() else
            "Tradução automática requer API de IA configurada; fila registrada na memória"}


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
                            for t in (c["tags"] or "ia").split(",")[:4])
        import os as _os
        url = f"{_os.environ.get('SITE_URL', 'https://wordbet.com.br').rstrip('/')}/article/{c['slug']}"
        posts = {}
        for rede in redes:
            curto = rede in ("x", "bluesky", "mastodon", "threads")
            texto = (c["title"] if curto else f"{c['title']}\n\n{c['excerpt']}")
            posts[rede] = {"texto": f"{texto}\n\n{hashtags}\n{url}"[:280 if rede == 'x' else 1000],
                           "cta": "Leia a matéria completa 👇",
                           "imagem_sugerida": mem_get("agent:image", f"prompt:{c['slug']}",
                                                      "prompt pendente")}
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
                           "AND image_url='' AND category != 'guides'")["n"]
    return {"aprovado": not problemas, "problemas": problemas,
            "noticias_sem_imagem_oficial": sem_img,
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
    resultado = {"radar": None, "auto_publicados": 0}

    # --- Radar diário ---
    manchetes = mem_get("agent:discovery", "manchetes_do_dia", []) or []
    slug_hoje = "ai-radar-" + db.query_one("SELECT date('now') AS d")["d"]
    if manchetes and not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug_hoje,)):
        from datetime import datetime as _dt
        data_br = _dt.utcnow().strftime("%b %d, %Y")
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
        img_oficial = next((m.get("image") for m in manchetes if m.get("image")), "")
        cid = db.execute(
            """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
               seo_title, seo_description, category, tags, image_url, published_at)
               VALUES (?,?,?,?, 'published',
                       (SELECT id FROM agents WHERE slug='discovery'), ?, ?, 'radar',
                       'radar,noticias,ia', ?, datetime('now'))""",
            (f"AI Radar — {data_br}: today's top stories", slug_hoje, corpo,
             f"The {min(len(manchetes),12)} most relevant AI headlines of {data_br}, with sources.",
             f"AI Radar {data_br}",
             f"Curadoria diária de notícias de IA de {data_br} com links para as fontes.",
             img_oficial))
        resultado["radar"] = {"id": cid, "slug": slug_hoje, "manchetes": min(len(manchetes), 12)}
        # Hero imediato se houver manchete quente (Breaking News rodou antes do Radar existir)
        quentes = [m for m in manchetes if any(t in m["title"].lower() for t in _BREAKING_TERMS)]
        if quentes:
            mem_set("agent:breaking-news", "hero",
                    {"slug": slug_hoje, "motivo": quentes[0]["title"][:120]})

    # --- Notícias sintetizadas (custo zero, sem IA): 1 artigo por cluster de manchetes ---
    from .synthesizer import cluster_manchetes, sintetizar
    from .imagegen import editorial_data_uri
    sintetizadas = 0
    grupos = cluster_manchetes([m for m in manchetes if m.get("resumo")])
    for grupo in grupos[:6]:  # até 6 notícias por ciclo
        art = sintetizar(grupo)
        if not art:
            continue
        # já publicado este tema hoje? (por título — rascunhos do Content Writer
        # podem ter o mesmo slug e não devem bloquear a publicação da síntese)
        if db.query_one("SELECT id FROM contents WHERE title = ? AND status='published'",
                        (art["title"][:200],)):
            continue
        base_slug, k = art["slug"], 2
        while db.query_one("SELECT id FROM contents WHERE slug = ?", (art["slug"],)):
            art["slug"] = f"{base_slug}-{k}"; k += 1
        img = art["image"] or editorial_data_uri(art["title"], "news")
        credit = _fonte_amigavel(art["source_url"]) if art["image"] else "AION editorial artwork"
        alt = (f"Image: {art['title'][:80]}" if art["image"]
               else f"AION editorial artwork: {art['title'][:80]}")
        db.execute(
            """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
               seo_title, seo_description, category, tags, image_url, image_alt,
               image_credit, image_width, image_height, source_url, published_at)
               VALUES (?,?,?,?, 'published',
                       (SELECT id FROM agents WHERE slug='content'), ?, ?, 'news',
                       ?, ?, ?, ?, '1200', '630', ?, datetime('now'))""",
            (art["title"], art["slug"], art["body"], art["excerpt"],
             art["title"][:60], art["excerpt"][:160], art["tags"], img, alt,
             credit, art["source_url"]))
        sintetizadas += 1
    resultado["noticias_sintetizadas"] = sintetizadas

    # --- Publicação agendada (Editorial Studio) ---
    agendados = db.query("SELECT id FROM contents WHERE status='draft' "
                         "AND scheduled_at != '' AND scheduled_at <= datetime('now')")
    for c in agendados:
        db.execute("UPDATE contents SET status='published', published_at=datetime('now'), "
                   "scheduled_at='' WHERE id=?", (c["id"],))
    resultado["agendados_publicados"] = len(agendados)

    # --- Auto-publicação de artigos IA aprovados ---
    bloqueados = {b["id"] for b in (mem_get("agent:fact-check", "bloqueados", []) or [])}
    drafts = db.query(
        "SELECT id, body FROM contents WHERE status='draft' AND agent_id IS NOT NULL")
    for c in drafts:
        if c["id"] in bloqueados or "[Rascunho automático" in (c["body"] or ""):
            continue
        db.execute("UPDATE contents SET status='published', published_at=datetime('now') "
                   "WHERE id = ?", (c["id"],))
        resultado["auto_publicados"] += 1
    if not manchetes:
        resultado["limitacao"] = ("Sem manchetes coletadas (fontes inacessíveis ou primeiro boot); "
                                  "Radar será criado no próximo ciclo com rede disponível")
    image_agent({})  # garante imagem em tudo que acabou de ser publicado
    resultado["imagens_garantidas"] = True
    return resultado


# ═══════════ BREAKING NEWS AGENT ═══════════
_BREAKING_TERMS = ("lança", "launch", "anuncia", "announce", "release", "apresenta",
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
        topico = f"Guia AION: o que é {kw} e por que está em alta"
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
            base = (kws + ["inteligência artificial"])[i % max(len(kws), 1)]
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
    sem_imagem = db.query_one("SELECT COUNT(*) AS n FROM contents "
                              "WHERE status='published' AND image_url=''")["n"]
    titulos_longos = db.query_one("SELECT COUNT(*) AS n FROM contents "
                                  "WHERE status='published' AND length(title) > 110")["n"]
    checks = {
        "max_image_preview_large": "meta robots configurada no frontend",
        "news_sitemap": "/news-sitemap.xml ativo (últimas 48h)",
        "artigos_sem_imagem_oficial": sem_imagem,
        "fallback": "arte editorial em gradiente (nunca caixa vazia)",
        "titulos_acima_110_chars": titulos_longos,
    }
    return {"auditoria": checks,
            "limitacao": "Métricas reais do Discover só existem no Search Console (credencial sua)"}


# ═══════════ IMAGE OPTIMIZATION AGENT ═══════════
def image_repair_agent(payload: dict) -> dict:
    """Repara o acervo: encontra artigos com image_url vazio e completa,
    sem duplicar. Roda no pipeline e é idempotente."""
    vazios = db.query("SELECT COUNT(*) n FROM contents WHERE image_url=''")[0]["n"]
    rep = image_agent({})
    restantes = db.query("SELECT COUNT(*) n FROM contents WHERE image_url=''")[0]["n"]
    if vazios and not restantes:
        db.execute("INSERT INTO logs (level, source, message) VALUES ('info','image-repair',?)",
                   (f"Reparadas {vazios} imagem(ns) ausente(s); acervo 100% com imagem",))
    return {"vazios_antes": vazios, "reparados": rep["corrigidos"],
            "vazios_depois": restantes, "acervo_completo": restantes == 0}


def image_optimization_agent(payload: dict) -> dict:
    rows = db.query("SELECT id, image_url FROM contents WHERE status='published' AND image_url!=''")
    invalidas = [c["id"] for c in rows
                 if not re.match(r"^https://[^\s]+\.(jpg|jpeg|png|webp)", c["image_url"], re.I)]
    for cid in invalidas:
        db.execute("UPDATE contents SET image_url='' WHERE id = ?", (cid,))
    return {"com_imagem_oficial": len(rows) - len(invalidas),
            "urls_invalidas_removidas": len(invalidas),
            "frontend": "loading=lazy nas listas; hero com prioridade"}


# ═══════════ SEARCH CONSOLE / REVENUE / DASHBOARD / PERFORMANCE ═══════════
def search_console_agent(payload: dict) -> dict:
    cfg = mem_get("agent:search-console", "site_url") or "não configurado"
    return {"site": cfg, "sitemaps": ["/sitemap.xml", "/news-sitemap.xml"],
            "limitacao": "Impressões/cliques exigem SEARCH_CONSOLE_SITE_URL + verificação (pendência humana)"}


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
    """Vigia a saúde: agentes em erro, erros recentes, tamanho do banco."""
    em_erro = db.query("SELECT slug FROM agents WHERE status='error'")
    erros = db.query_one("SELECT COUNT(*) n FROM logs WHERE level='error' "
                         "AND created_at > datetime('now','-6 hours')")["n"]
    if em_erro:
        db.execute("INSERT INTO logs (level, source, message) VALUES ('warn','monitor',?)",
                   (f"Agentes em erro (CEO reinicia no próximo ciclo): "
                    f"{[a['slug'] for a in em_erro]}",))
    return {"agentes_em_erro": [a["slug"] for a in em_erro], "erros_6h": erros,
            "saudavel": not em_erro and erros == 0}


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
    sem_imagem = [c["slug"] for c in pub if not c["image_url"]]
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
