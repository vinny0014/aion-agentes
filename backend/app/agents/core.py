"""Núcleo da arquitetura multiagente: execução isolada, retry, logs, métricas,
memória compartilhada e controle de orçamento."""
import json
import time
import traceback

from ..core import database as db

MAX_RETRIES = 2


# ---------- memória compartilhada (tabela memories) ----------
def mem_get(scope: str, key: str, default=None):
    row = db.query_one("SELECT value FROM memories WHERE scope = ? AND key = ?", (scope, key))
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return row["value"]


def mem_set(scope: str, key: str, value) -> None:
    db.execute(
        """INSERT INTO memories (scope, key, value) VALUES (?,?,?)
           ON CONFLICT(scope, key)
           DO UPDATE SET value = excluded.value, updated_at = datetime('now')""",
        (scope, key, json.dumps(value, ensure_ascii=False, default=str)),
    )


# ---------- orçamento (Cost Guard integra aqui) ----------
def budget_remaining() -> float:
    """Orçamento diário (USD) menos gasto registrado hoje em agent_runs."""
    row = db.query_one("SELECT value FROM app_settings WHERE key = 'orcamento_diario_usd'")
    budget = float(row["value"]) if row else 5.0  # padrão conservador
    spent = db.query_one(
        "SELECT COALESCE(SUM(cost),0) AS c FROM agent_runs WHERE date(created_at)=date('now')"
    )["c"]
    return budget - spent


def record_cost(agent_slug: str, tokens: int, cost: float) -> None:
    db.execute(
        "UPDATE agent_runs SET tokens = tokens + ?, cost = cost + ? "
        "WHERE id = (SELECT MAX(id) FROM agent_runs WHERE agent_slug = ?)",
        (tokens, cost, agent_slug),
    )


# ---------- execução isolada com retry, log e métricas ----------
def run_agent(slug: str, fn, payload: dict | None = None) -> dict:
    """Executa um agente com isolamento de falha, retry e registro completo.
    Nunca propaga exceção — falha de um agente não derruba o pipeline."""
    payload = payload or {}
    start = time.time()
    retries = 0
    last_error = None
    db.execute("UPDATE agents SET status = 'running' WHERE slug = ?", (slug,))
    while retries <= MAX_RETRIES:
        try:
            output = fn(payload) or {}
            dur = int((time.time() - start) * 1000)
            db.execute(
                """INSERT INTO agent_runs (agent_slug, status, input, output, retries, duration_ms)
                   VALUES (?,?,?,?,?,?)""",
                (slug, "ok", json.dumps(payload, default=str)[:2000],
                 json.dumps(output, ensure_ascii=False, default=str)[:4000], retries, dur),
            )
            db.execute("UPDATE agents SET status = 'idle' WHERE slug = ?", (slug,))
            return {"agent": slug, "status": "ok", "retries": retries,
                    "duration_ms": dur, "output": output}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            retries += 1
            time.sleep(min(0.2 * retries, 1.0))  # backoff curto
    dur = int((time.time() - start) * 1000)
    db.execute(
        """INSERT INTO agent_runs (agent_slug, status, input, error, retries, duration_ms)
           VALUES (?,?,?,?,?,?)""",
        (slug, "error", json.dumps(payload, default=str)[:2000],
         (last_error or "")[:1500] + " | " + traceback.format_exc()[-500:],
         retries - 1, dur),
    )
    db.execute("UPDATE agents SET status = 'error' WHERE slug = ?", (slug,))
    db.execute(
        "INSERT INTO logs (level, source, message) VALUES ('error', ?, ?)",
        (slug, f"Agente falhou após {retries} tentativa(s): {last_error}"),
    )
    return {"agent": slug, "status": "error", "retries": retries - 1,
            "duration_ms": dur, "error": last_error}


def agent_metrics(slug: str | None = None) -> list[dict]:
    where = "WHERE agent_slug = ?" if slug else ""
    params = (slug,) if slug else ()
    return db.query(
        f"""SELECT agent_slug,
                   COUNT(*) AS execucoes,
                   SUM(status = 'ok') AS sucessos,
                   SUM(status = 'error') AS falhas,
                   ROUND(AVG(duration_ms)) AS duracao_media_ms,
                   SUM(tokens) AS tokens, ROUND(SUM(cost), 4) AS custo_usd
            FROM agent_runs {where} GROUP BY agent_slug ORDER BY agent_slug""", params)
