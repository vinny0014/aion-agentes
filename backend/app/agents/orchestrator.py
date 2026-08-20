"""CEO MASTER + SCHEDULER — orquestração do pipeline multiagente.

Ordem do pipeline, trava de concorrência, guarda anti-loop, reinício de
agentes com falha e respeito ao orçamento (Cost Guard antes de etapas de IA).
"""
from datetime import datetime, timezone

from ..core import database as db
from . import team
from .core import budget_remaining, mem_get, mem_set, run_agent

PIPELINE = [
    ("discovery", team.discovery_agent, False),
    ("research", team.research_agent, False),
    ("trend-hunter", team.trend_hunter_agent, False),
    ("breaking-news", team.breaking_news_agent, False),
    ("content", team.content_writer_agent, True),
    ("seo", team.seo_agent, False),
    ("image", team.image_agent, False),
    ("image-prompt", team.image_prompt_agent, False),
    ("image-repair", team.image_repair_agent, False),
    ("image-optimization", team.image_optimization_agent, False),
    ("image-quality", team.image_quality_agent, False),
    ("fact-check", team.fact_check_agent, False),
    ("publisher", team.publisher_agent, False),
    ("dashboard", team.dashboard_agent, False),
    ("google-discover", team.google_discover_agent, False),
    ("google-news", team.google_news_agent, False),
    ("rss", team.rss_agent, False),
    ("newsletter", team.newsletter_agent, False),
    ("social-media", team.social_media_agent, False),
    ("translation", team.translation_agent, True),
    ("analytics", team.analytics_agent, False),
    ("discovery-growth", team.discovery_growth_agent, False),
    ("search-console", team.search_console_agent, False),
    ("adsense-opt", team.adsense_agent, False),
    ("revenue", team.revenue_agent, False),
    ("cost-guard", team.cost_guard_agent, False),
    ("performance", team.performance_agent, False),
    ("qa", team.qa_agent, False),
    ("security", team.security_agent, False),
    ("monitor", team.monitor_agent, False),
]

MAX_CYCLES_PER_HOUR = 4  # guarda anti-loop
LOCK_TTL_SECONDS = 30 * 60


def restart_failed_agents() -> int:
    rows = db.query("SELECT slug FROM agents WHERE status = 'error'")
    for r in rows:
        db.execute("UPDATE agents SET status = 'idle' WHERE slug = ?", (r["slug"],))
    return len(rows)


def run_cycle(trigger: str = "manual") -> dict:
    """Um ciclo completo do pipeline. Nunca roda concorrente; nunca em loop."""
    now = datetime.now(timezone.utc).timestamp()
    lock = mem_get("agent:ceo-master", "lock") or {}
    if isinstance(lock, dict) and lock.get("state") == "on":
        age = now - float(lock.get("acquired_at") or 0)
        if 0 <= age < LOCK_TTL_SECONDS:
            return {"status": "skipped", "motivo": "ciclo já em execução"}
        db.execute(
            "INSERT INTO logs (level,source,message) VALUES ('warn','ceo-master',?)",
            (f"Recovered stale orchestrator lock after {int(max(age, 0))} seconds",),
        )
    # guarda anti-loop
    recentes = db.query_one(
        "SELECT COUNT(*) AS n FROM agent_runs WHERE agent_slug='ceo-master' "
        "AND created_at > datetime('now','-1 hour')")["n"]
    if recentes >= MAX_CYCLES_PER_HOUR:
        return {"status": "skipped", "motivo": f"limite de {MAX_CYCLES_PER_HOUR} ciclos/hora"}

    mem_set("agent:ceo-master", "lock", {
        "state": "on", "acquired_at": now, "trigger": trigger,
    })
    try:
        reiniciados = restart_failed_agents()
        resultados = []
        for slug, fn, usa_ia in PIPELINE:
            if usa_ia and budget_remaining() <= 0:
                resultados.append({"agent": slug, "status": "skipped",
                                   "motivo": "orçamento diário esgotado (Cost Guard)"})
                continue
            resultados.append(run_agent(slug, fn))
        resumo = {
            "trigger": trigger,
            "agentes_reiniciados": reiniciados,
            "ok": sum(1 for r in resultados if r["status"] == "ok"),
            "erros": sum(1 for r in resultados if r["status"] == "error"),
            "pulados": sum(1 for r in resultados if r["status"] == "skipped"),
            "etapas": resultados,
        }
        db.execute(
            "INSERT INTO agent_runs (agent_slug, status, input, output) VALUES "
            "('ceo-master','ok',?,?)",
            (trigger, f"ok={resumo['ok']} erros={resumo['erros']} pulados={resumo['pulados']}"))
        return resumo
    finally:
        mem_set("agent:ceo-master", "lock", {
            "state": "off", "released_at": datetime.now(timezone.utc).timestamp(),
        })
