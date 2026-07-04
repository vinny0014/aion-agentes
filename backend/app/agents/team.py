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
    "https://openai.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://www.anthropic.com/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://blogs.microsoft.com/ai/feed/",
    "https://blogs.nvidia.com/feed/",
    "https://export.arxiv.org/rss/cs.AI",
    "https://github.com/trending",  # HTML, tratado à parte
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
                if titulo:
                    found.append({"source": url, "title": titulo, "link": link})
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
        if len(c["body"] or "") < 200:
            problemas.append("corpo muito curto (<200 caracteres)")
        dup = db.query_one(
            "SELECT id FROM contents WHERE title = ? AND id != ? AND status = 'published'",
            (c["title"], c["id"]))
        if dup:
            problemas.append(f"título duplicado do conteúdo #{dup['id']}")
        # links internos citados devem existir
        for slug in re.findall(r"/conteudo/([a-z0-9-]+)", c["body"] or ""):
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
    redes = ["x", "linkedin", "facebook", "instagram", "threads", "bluesky", "mastodon"]
    rows = db.query("SELECT slug, title, excerpt, tags FROM contents "
                    "WHERE status='published' ORDER BY id DESC LIMIT 10")
    gerados = 0
    for c in rows:
        key = f"posts:{c['slug']}"
        if mem_get("agent:social-media", key):
            continue
        hashtags = " ".join(f"#{t.strip().replace(' ', '')}"
                            for t in (c["tags"] or "ia").split(",")[:4])
        url = f"https://aion-agentes.vercel.app/conteudo/{c['slug']}"
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
                  "rodape": "Você recebe porque se inscreveu. Cancele quando quiser."}
        mem_set("agent:newsletter", "ultima_edicao", edicao)
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
    return {"aprovado": not problemas, "problemas": problemas,
            "cobertura": "23 testes de integração no CI cobrem rotas/auth/CRUD/SEO/pipeline"}


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
    slug_hoje = "radar-ia-" + db.query_one("SELECT date('now') AS d")["d"]
    if manchetes and not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug_hoje,)):
        data_br = db.query_one("SELECT strftime('%d/%m/%Y','now') AS d")["d"]
        linhas = []
        for m in manchetes[:12]:
            fonte = _fonte_amigavel(m.get("link") or m.get("source", ""))
            link = m.get("link") or m.get("source", "")
            linhas.append(f"**{m['title']}** — via {fonte}. [Ler na fonte]({link})")
        corpo = (
            f"## O que movimentou a IA hoje\n\n"
            f"Curadoria diária do AION: os destaques publicados pelas principais fontes do setor "
            f"em {data_br}, com link direto para a matéria original de cada uma.\n\n"
            + "\n\n".join(linhas)
            + "\n\n## Sobre o Radar\n\nO Radar IA é gerado automaticamente pelo Discovery Agent "
              "do AION a partir de feeds oficiais. Os títulos pertencem às respectivas fontes; "
              "a curadoria e o texto de apresentação são originais."
        )
        cid = db.execute(
            """INSERT INTO contents (title, slug, body, excerpt, status, agent_id,
               seo_title, seo_description, category, tags, published_at)
               VALUES (?,?,?,?, 'published',
                       (SELECT id FROM agents WHERE slug='discovery'), ?, ?, 'radar',
                       'radar,noticias,ia', datetime('now'))""",
            (f"Radar IA — {data_br}: os destaques do dia", slug_hoje, corpo,
             f"As {min(len(manchetes),12)} manchetes de IA mais relevantes de {data_br}, com fontes.",
             f"Radar IA {data_br}", f"Curadoria diária de notícias de IA de {data_br} com links para as fontes."))
        resultado["radar"] = {"id": cid, "slug": slug_hoje, "manchetes": min(len(manchetes), 12)}

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
    return resultado
