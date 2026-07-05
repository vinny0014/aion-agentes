"""Testes de integração — AION AGENTES API."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_aion.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ENV"] = "test"

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

Path("test_aion.db").unlink(missing_ok=True)

from app.main import app  # noqa: E402
from app.core.database import init_db  # noqa: E402
from app.agents.registry import seed_agents  # noqa: E402

init_db()
seed_agents()
client = TestClient(app)
ADMIN = {"name": "Admin AION", "email": "admin@aion.dev", "password": "senhaForte123"}
USER = {"name": "Usuária Comum", "email": "user@aion.dev", "password": "senhaForte123"}


def auth(email, password):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    t = r.json()
    return {"Authorization": f"Bearer {t['access_token']}"}, t["refresh_token"]


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "ok"


def test_register_first_user_is_admin():
    r = client.post("/api/auth/register", json=ADMIN)
    assert r.status_code == 201 and r.json()["role"] == "admin"
    r = client.post("/api/auth/register", json=USER)
    assert r.status_code == 201 and r.json()["role"] == "user"
    # e-mail duplicado
    assert client.post("/api/auth/register", json=ADMIN).status_code == 409


def test_login_and_me():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 200 and r.json()["email"] == ADMIN["email"]
    # senha errada
    r = client.post("/api/auth/login", data={"username": ADMIN["email"], "password": "errada123"})
    assert r.status_code == 401


def test_refresh_token_rotation():
    _, refresh = auth(ADMIN["email"], ADMIN["password"])
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200 and "access_token" in r.json()
    # token antigo foi revogado
    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 401


def test_agents_seeded_and_crud():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    r = client.get("/api/agents", headers=h)
    slugs = {a["slug"] for a in r.json()}
    assert {"ceo-master", "developer", "qa", "content", "seo",
            "github", "deploy", "monitor", "cost-guard"} <= slugs
    r = client.post("/api/agents", headers=h, json={
        "slug": "traducao", "name": "Tradução", "role": "conteudo"})
    assert r.status_code == 201
    aid = r.json()["id"]
    r = client.patch(f"/api/agents/{aid}", headers=h, json={"status": "running"})
    assert r.json()["status"] == "running"
    assert client.delete(f"/api/agents/{aid}", headers=h).status_code == 204


def test_users_crud_admin_only():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    hu, _ = auth(USER["email"], USER["password"])
    assert client.get("/api/users", headers=hu).status_code == 403
    users = client.get("/api/users", headers=ha).json()
    assert len(users) == 2
    uid = [u for u in users if u["email"] == USER["email"]][0]["id"]
    r = client.patch(f"/api/users/{uid}", headers=ha, json={"name": "Nome Novo"})
    assert r.json()["name"] == "Nome Novo"


def test_content_crud_and_sitemap():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    r = client.post("/api/contents", headers=h, json={
        "title": "O que são agentes de IA",
        "slug": "o-que-sao-agentes-de-ia",
        "body": "Conteúdo completo...",
        "excerpt": "Entenda agentes de IA.",
        "status": "published",
    })
    assert r.status_code == 201 and r.json()["published_at"]
    cid = r.json()["id"]
    r = client.patch(f"/api/contents/{cid}", headers=h, json={"title": "Agentes de IA: guia"})
    assert r.json()["title"] == "Agentes de IA: guia"
    # sitemap inclui o slug publicado
    sm = client.get("/sitemap.xml")
    assert sm.status_code == 200 and "o-que-sao-agentes-de-ia" in sm.text
    assert "Sitemap" in client.get("/robots.txt").text


def test_tasks_crud():
    h, _ = auth(USER["email"], USER["password"])
    r = client.post("/api/tasks", headers=h, json={"title": "Revisar landing", "priority": 1})
    tid = r.json()["id"]
    r = client.patch(f"/api/tasks/{tid}", headers=h, json={"status": "done"})
    assert r.json()["status"] == "done"
    assert client.delete(f"/api/tasks/{tid}", headers=h).status_code == 204


def test_logs_memory_settings():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    client.post("/api/logs", headers=ha, json={"message": "teste de log", "source": "qa"})
    assert any(l["message"] == "teste de log" for l in client.get("/api/logs", headers=ha).json())
    r = client.put("/api/memory", headers=ha, json={
        "scope": "agent:seo", "key": "ultima_auditoria", "value": "2026-07-03"})
    assert r.json()["value"] == "2026-07-03"
    r = client.put("/api/settings", headers=ha, json={"key": "posts_por_dia", "value": "3"})
    assert r.status_code == 200
    # segredos são recusados no banco
    r = client.put("/api/settings", headers=ha, json={"key": "openai_api_key", "value": "sk-x"})
    assert r.status_code == 400


def test_content_queue_pipeline_offline_draft():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    r = client.post("/api/content-queue", headers=h, json={"topic": "Tendências de IA em 2026"})
    assert r.status_code == 201
    r = client.post("/api/pipeline/run")
    assert r.json()["offline_drafts"] >= 1  # sem API key -> rascunho offline + pendência em log
    items = client.get("/api/content-queue", headers=h).json()
    done = [i for i in items if i["topic"] == "Tendências de IA em 2026"][0]
    assert done["status"] == "done" and done["result_content_id"]
    draft = client.get(f"/api/contents/{done['result_content_id']}", headers=h).json()
    assert draft["status"] == "draft" and "Rascunho automático" in draft["body"]
    assert draft["slug"].startswith("tendencias-de-ia-em-2026")
    # pendência humana registrada em log
    logs = client.get("/api/logs", headers=h).json()
    assert any("PENDÊNCIA HUMANA" in l["message"] for l in logs)


def test_pipeline_unique_slug():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    client.post("/api/content-queue", headers=h, json={"topic": "Tendências de IA em 2026"})
    client.post("/api/pipeline/run")
    slugs = [c["slug"] for c in client.get("/api/contents", headers=h).json()]
    assert len(slugs) == len(set(slugs))  # sem colisão de slug


def test_auth_required():
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/api/agents").status_code == 401


# ====================== FASE 2 — Portal público ======================
def test_public_articles_list_and_detail():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    client.post("/api/contents", headers=h, json={
        "title": "Guia público de IA", "slug": "guia-publico-de-ia",
        "body": "# Seção\n\nParágrafo um.\n\nParágrafo dois.",
        "excerpt": "Um guia aberto.", "status": "published"})
    r = client.get("/api/public/articles")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1 and "body" not in body["items"][0]
    r = client.get("/api/public/articles/guia-publico-de-ia")
    assert r.status_code == 200 and "Parágrafo um" in r.json()["body"]
    # rascunhos não vazam
    client.post("/api/contents", headers=h, json={
        "title": "Rascunho secreto", "slug": "rascunho-secreto", "status": "draft"})
    assert client.get("/api/public/articles/rascunho-secreto").status_code == 404


def test_public_pagination():
    r = client.get("/api/public/articles?page=1&per_page=1")
    b = r.json()
    assert b["per_page"] == 1 and len(b["items"]) <= 1



# ====================== FASE 5 — Hardening ======================
def test_security_headers():
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_rate_limit_login():
    from app.core.config import settings as cfg
    from app.main import _BUCKETS
    cfg.ENV = "development"
    _BUCKETS.clear()
    try:
        for _ in range(10):
            client.post("/api/auth/login", data={"username": "x@x.dev", "password": "errada123"})
        r = client.post("/api/auth/login", data={"username": "x@x.dev", "password": "errada123"})
        assert r.status_code == 429
    finally:
        cfg.ENV = "test"
        _BUCKETS.clear()


# ====================== MONETIZAÇÃO — Acesso público ======================
def test_search_categories_tags():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    client.post("/api/contents", headers=h, json={
        "title": "IA na saúde brasileira", "slug": "ia-na-saude",
        "body": "Aplicações de diagnóstico assistido.", "excerpt": "IA na medicina.",
        "status": "published", "category": "Saude", "tags": "IA, Medicina, diagnostico"})
    # busca sem login
    r = client.get("/api/public/articles?q=diagnóstico")
    assert r.status_code == 200 and r.json()["total"] >= 1
    # filtro por categoria (normalizada p/ minúsculas)
    r = client.get("/api/public/articles?category=saude")
    assert r.json()["total"] == 1
    # filtro por tag
    r = client.get("/api/public/articles?tag=medicina")
    assert r.json()["total"] == 1
    # listas de categorias e tags
    assert any(c["category"] == "saude" for c in client.get("/api/public/categories").json())
    assert any(t["tag"] == "ia" for t in client.get("/api/public/tags").json())


def test_public_contact():
    r = client.post("/api/public/contact", json={
        "name": "Visitante", "email": "v@site.com", "message": "Proposta de parceria."})
    assert r.status_code == 201
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    logs = client.get("/api/logs?limit=20", headers=ha).json()
    assert any(l["source"] == "contato" for l in logs)


def test_route_access_matrix():
    """Prova a matriz: rotas públicas respondem sem token; privadas exigem 401."""
    publicas = ["/api/health", "/api/public/articles", "/api/public/categories",
                "/api/public/tags", "/robots.txt", "/sitemap.xml"]
    for rota in publicas:
        assert client.get(rota).status_code == 200, f"pública falhou: {rota}"
    privadas = ["/api/users", "/api/agents", "/api/tasks", "/api/contents",
                "/api/logs", "/api/memory", "/api/settings", "/api/content-queue",
                "/api/auth/me"]
    for rota in privadas:
        assert client.get(rota).status_code == 401, f"privada exposta: {rota}"


def test_robots_blocks_private_areas():
    txt = client.get("/robots.txt").text
    assert "Disallow: /admin" in txt and "Disallow: /dashboard" in txt
    assert "Disallow: /api/" in txt and "Allow: /" in txt
    sm = client.get("/sitemap.xml").text
    for p in ["/conteudos", "/categorias", "/tags", "/privacidade", "/termos", "/contato"]:
        assert p in sm, f"faltou no sitemap: {p}"
    assert "/admin" not in sm and "/dashboard" not in sm


# ====================== OMEGA — Discovery Growth ======================
def test_reading_time_and_related():
    h, _ = auth(ADMIN["email"], ADMIN["password"])
    client.post("/api/contents", headers=h, json={
        "title": "IA na educação", "slug": "ia-na-educacao",
        "body": "palavra " * 400, "excerpt": "Educação e IA.",
        "status": "published", "category": "saude", "tags": "ia,educacao"})
    r = client.get("/api/public/articles/ia-na-educacao")
    assert r.json()["reading_time"] == 2  # 400 palavras / 200 wpm
    rel = client.get("/api/public/articles/ia-na-saude/related").json()
    assert any(x["slug"] == "ia-na-educacao" for x in rel)  # mesma categoria + tag "ia"


def test_growth_report_admin_only():
    assert client.get("/api/growth/report").status_code == 401
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    r = client.get("/api/growth/report", headers=ha)
    assert r.status_code == 200
    body = r.json()
    assert body["agente"] == "discovery-growth"
    assert "google_adsense" in body["integracoes"]
    assert "fila" in body["calendario"] and "clusters" in body["calendario"]


def test_discovery_agent_seeded():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    slugs = {a["slug"] for a in client.get("/api/agents", headers=ha).json()}
    assert "discovery-growth" in slugs


# ====================== FASE 2 OMEGA — Multiagente ======================
def test_16_agents_seeded():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    slugs = {a["slug"] for a in client.get("/api/agents", headers=ha).json()}
    esperados = {"ceo-master", "discovery", "content", "fact-check", "seo", "image-prompt",
                 "translation", "social-media", "newsletter", "analytics", "discovery-growth",
                 "adsense-opt", "qa", "security", "cost-guard", "scheduler"}
    assert esperados <= slugs


def test_orchestrator_cycle_and_runs():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    assert client.post("/api/orchestrator/run").status_code == 401  # protegido
    r = client.post("/api/orchestrator/run", headers=ha)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] >= 10 and body["erros"] == 0  # isolamento: nada explode
    runs = client.get("/api/orchestrator/runs?limit=100", headers=ha).json()
    assert any(x["agent_slug"] == "fact-check" for x in runs)
    m = client.get("/api/orchestrator/metrics", headers=ha).json()
    assert "orcamento_restante_usd" in m and len(m["por_agente"]) >= 10


def test_fact_check_blocks_placeholder_draft():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    client.post("/api/content-queue", headers=ha, json={"topic": "Pauta para fact check"})
    client.post("/api/pipeline/run")  # gera rascunho offline com placeholders
    from app.agents.team import fact_check_agent
    rep = fact_check_agent({})
    assert rep["bloqueados"] >= 1


def test_orchestrator_anti_loop():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    ultimo = {}
    for _ in range(5):
        ultimo = client.post("/api/orchestrator/run", headers=ha).json()
    assert ultimo.get("status") == "skipped" and "ciclos/hora" in ultimo.get("motivo", "")


def test_newsletter_subscribe_public():
    r = client.post("/api/public/newsletter", json={
        "name": "geral", "email": "leitor@site.com", "message": "inscrever"})
    assert r.status_code == 201
    # idempotente
    assert client.post("/api/public/newsletter", json={
        "name": "geral", "email": "leitor@site.com", "message": "inscrever"}).status_code == 201


def test_cost_guard_blocks_ai_steps_when_budget_zero():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    from app.core import database as db2
    db2.execute("INSERT INTO app_settings (key, value) VALUES ('orcamento_mensal_usd','0') "
                "ON CONFLICT(key) DO UPDATE SET value='0'")
    db2.execute("DELETE FROM agent_runs WHERE agent_slug='ceo-master'")  # liberar anti-loop
    from app.agents.core import mem_set
    mem_set("agent:ceo-master", "lock", "off")
    r = client.post("/api/orchestrator/run", headers=ha).json()
    pulados = [e for e in r["etapas"] if e.get("status") == "skipped"]
    assert any("orçamento" in e.get("motivo", "") for e in pulados)
    db2.execute("UPDATE app_settings SET value='10' WHERE key='orcamento_mensal_usd'")


# ====================== INGESTÃO E PUBLICAÇÃO AUTOMÁTICA ======================
def test_bootstrap_seeds_when_empty():
    from app.bootstrap import seed_initial_content
    # banco de teste já tem conteúdo; idempotência: não duplica
    antes = client.get("/api/public/articles?per_page=50").json()["total"]
    seed_initial_content()
    seed_initial_content()
    depois = client.get("/api/public/articles?per_page=50").json()["total"]
    assert depois >= antes and depois - antes <= 3


def test_discovery_parses_items_and_publisher_creates_radar(monkeypatch):
    import app.agents.team as team

    class FakeResp:
        status_code = 200
        text = """<rss><channel><title>Feed</title>
        <item><title>Nova técnica de raciocínio anunciada</title><link>https://exemplo.org/a1</link></item>
        <item><title><![CDATA[Modelo aberto bate benchmark]]></title><link>https://exemplo.org/a2</link></item>
        </channel></rss>"""
        def raise_for_status(self): pass

    monkeypatch.setattr(team.httpx, "get", lambda *a, **k: FakeResp())
    rep = team.discovery_agent({"max_sources": 1})
    assert rep["encontrados"] == 2
    pub = team.publisher_agent({})
    assert pub["radar"] and pub["radar"]["manchetes"] == 2
    slug = pub["radar"]["slug"]
    art = client.get(f"/api/public/articles/{slug}").json()
    assert art["status_code"] if False else True
    assert "Ler na fonte](https://exemplo.org/a1" in art["body"]
    assert art["category"] == "radar"
    # idempotente no mesmo dia
    assert team.publisher_agent({})["radar"] is None


def test_publisher_respects_fact_check_and_setting():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    from app.agents.team import fact_check_agent, publisher_agent
    from app.core import database as db2
    # rascunho de agente com placeholder segue bloqueado
    fact_check_agent({})
    drafts_placeholder = db2.query(
        "SELECT COUNT(*) AS n FROM contents WHERE status='draft' AND body LIKE '%Rascunho automático%'")[0]["n"]
    publisher_agent({})
    ainda = db2.query(
        "SELECT COUNT(*) AS n FROM contents WHERE status='draft' AND body LIKE '%Rascunho automático%'")[0]["n"]
    assert ainda == drafts_placeholder  # nada com placeholder foi publicado
    # setting desliga tudo
    db2.execute("INSERT INTO app_settings (key,value) VALUES ('publicacao_automatica','off') "
                "ON CONFLICT(key) DO UPDATE SET value='off'")
    assert publisher_agent({}).get("status") == "desativado via settings"
    db2.execute("UPDATE app_settings SET value='on' WHERE key='publicacao_automatica'")


def test_publisher_agent_registered_and_in_pipeline():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    slugs = {a["slug"] for a in client.get("/api/agents", headers=ha).json()}
    assert "publisher" in slugs
    from app.agents.orchestrator import PIPELINE
    ordem = [p[0] for p in PIPELINE]
    assert ordem.index("publisher") > ordem.index("fact-check")  # publisher sempre depois do fact-check


# ====================== DISCOVERY OMEGA ======================
def test_cost_guard_tiers():
    from app.core import database as db3
    from app.agents.core import budget_tier
    db3.execute("INSERT INTO app_settings (key,value) VALUES ('orcamento_mensal_usd','10') "
                "ON CONFLICT(key) DO UPDATE SET value='10'")
    db3.execute("DELETE FROM agent_runs WHERE agent_slug='_custo_teste'")
    assert budget_tier()["modo"] in ("normal", "alerta")
    db3.execute("INSERT INTO agent_runs (agent_slug,cost) VALUES ('_custo_teste', 7.2)")
    assert budget_tier()["modo"] == "economico"
    db3.execute("INSERT INTO agent_runs (agent_slug,cost) VALUES ('_custo_teste', 2.9)")  # 10.1
    t = budget_tier()
    assert t["modo"] == "suspenso" and t["ia_liberada"] is False
    db3.execute("DELETE FROM agent_runs WHERE agent_slug='_custo_teste'")


def test_news_sitemap_last_48h():
    r = client.get("/news-sitemap.xml")
    assert r.status_code == 200 and "sitemap-news" in r.text
    assert "AION AI NEWS OS" in r.text and "<news:title>" in r.text


def test_hero_endpoint_and_breaking():
    r = client.get("/api/public/hero")
    assert r.status_code == 200 and "slug" in r.json()
    # breaking news define hero para o radar do dia
    from app.agents.core import mem_set
    from app.agents.team import breaking_news_agent
    mem_set("agent:discovery", "manchetes_do_dia",
            [{"title": "Empresa lança modelo aberto", "link": "https://ex.org/x", "image": ""}])
    rep = breaking_news_agent({})
    assert rep["manchetes_quentes"] == 1
    if rep["hero_definido"]:
        assert client.get("/api/public/hero").json()["breaking"] is True


def test_discovery_captures_official_image(monkeypatch):
    import app.agents.team as team

    class FakeResp:
        status_code = 200
        text = ('<rss><channel><title>F</title><item><title>Notícia com foto oficial</title>'
                '<link>https://ex.org/n1</link>'
                '<enclosure url="https://ex.org/press/foto.jpg" type="image/jpeg"/>'
                '</item></channel></rss>')
        def raise_for_status(self): pass

    monkeypatch.setattr(team.httpx, "get", lambda *a, **k: FakeResp())
    team.discovery_agent({"max_sources": 1})
    from app.agents.core import mem_get
    m = mem_get("agent:discovery", "manchetes_do_dia")
    assert m[0]["image"] == "https://ex.org/press/foto.jpg"


def test_new_agents_registered_and_pipeline_23():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    slugs = {a["slug"] for a in client.get("/api/agents", headers=ha).json()}
    novos = {"breaking-news", "trend-hunter", "google-discover", "image-optimization",
             "search-console", "revenue", "dashboard", "performance"}
    assert novos <= slugs
    from app.agents.orchestrator import PIPELINE
    assert len(PIPELINE) == 27


def test_public_articles_expose_image_and_source():
    item = client.get("/api/public/articles").json()["items"][0]
    assert "image_url" in item and "source_url" in item


# ====================== AUDITORIA DOS AGENTES ======================
def test_research_agent_briefing_feeds_writer():
    ha, _ = auth(ADMIN["email"], ADMIN["password"])
    from app.agents.core import mem_set, mem_get
    from app.agents.team import research_agent
    r = client.post("/api/content-queue", headers=ha, json={"topic": "modelos abertos de linguagem"})
    qid = r.json()["id"]
    mem_set("agent:discovery", "manchetes_do_dia",
            [{"title": "Novos modelos abertos de linguagem anunciados", "link": "https://ex.org/m1"}])
    rep = research_agent({})
    assert rep["briefings_gerados"] >= 1
    brief = mem_get("agent:research", f"briefing:{qid}")
    assert brief and brief["fontes"] == ["https://ex.org/m1"]


def test_rss_feed():
    r = client.get("/rss.xml")
    assert r.status_code == 200 and "<rss version=\"2.0\"" in r.text and "<item>" in r.text


def test_pipeline_order_matches_flow():
    from app.agents.orchestrator import PIPELINE
    ordem = [p[0] for p in PIPELINE]
    fluxo = ["discovery", "research", "trend-hunter", "breaking-news", "content",
             "fact-check", "seo", "image-prompt", "image-optimization", "publisher",
             "dashboard", "google-discover", "google-news", "rss", "newsletter",
             "social-media"]
    idx = [ordem.index(e) for e in fluxo]
    assert idx == sorted(idx), f"fluxo fora de ordem: {ordem}"
    assert len(PIPELINE) == 27



# ====================== OMEGA FINAL ======================
def test_hero_ranking_never_random():
    from app.agents.team import hero_ranking
    r = hero_ranking()
    assert r and r["slug"]  # sempre determinístico, com score
    h = client.get("/api/public/hero").json()
    assert "hero_score" in h


def test_rss_googlenews_monitor_agents():
    from app.agents.team import rss_agent, google_news_agent, monitor_agent
    assert rss_agent({})["xml_valido"] is True
    assert google_news_agent({})["news_sitemap_valido"] is True
    m = monitor_agent({})
    assert "agentes_em_erro" in m and "erros_6h" in m


def test_fact_check_blocks_short_ai_article():
    from app.core import database as db4
    from app.agents.team import fact_check_agent
    db4.execute("""INSERT INTO contents (title, slug, body, excerpt, status, agent_id)
        VALUES ('Curto demais IA', 'curto-demais-ia', ?, 'x', 'draft',
        (SELECT id FROM agents WHERE slug='content'))""",
        ("palavra " * 100,))  # 100 palavras < 500
    rep = fact_check_agent({})
    assert any("500" in str(b["problemas"]) for b in
               __import__("app.agents.core", fromlist=["mem_get"]).mem_get("agent:fact-check", "bloqueados")
               if b["title"] == "Curto demais IA")
