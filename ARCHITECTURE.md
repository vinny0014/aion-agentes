# ARCHITECTURE.md — AION Agentes
**Camadas:** SPA React (Vite/TS/Tailwind) → API FastAPI → SQLite (camada isolada, pronta p/ PostgreSQL).
**Multiagente:** `agents/core.py` (execução isolada, retry, métricas, memória, orçamento) · `agents/team.py` (16 agentes) · `agents/orchestrator.py` (CEO+pipeline+locks) · `agents/registry.py` (seed+conteúdo) · `agents/providers.py` (OpenAI/Anthropic/OpenRouter/Gemini plugáveis) · `agents/discovery.py` (SEO/crescimento).
**Dados:** users, agents, contents, tasks, logs, memories (memória compartilhada), app_settings, refresh_tokens, content_queue, agent_runs (telemetria), subscribers.
**Resiliência:** falha de agente nunca propaga; retry 2x; anti-loop 4 ciclos/h; lock de concorrência; Cost Guard corta etapas de IA sem orçamento.
**Automação 24h:** scheduler roda fila (1h) e ciclo completo (6h); tudo também acionável via API.
