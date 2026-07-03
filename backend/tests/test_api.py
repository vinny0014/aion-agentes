"""Testes de integração — AION AGENTES API."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_aion.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

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
