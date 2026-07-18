# ARCHITECTURE.md — AION AI NEWS OS
**Camadas:** SPA React (Vite/TS/Tailwind) → API FastAPI → SQLite (camada isolada, pronta p/ PostgreSQL).
**Multiagente:** `agents/core.py` (execução isolada, retry, métricas, memória, orçamento) · `agents/team.py` (implementações operacionais) · `agents/orchestrator.py` (pipeline de 30 etapas + locks) · `agents/registry.py` (35 agentes registrados + conteúdo) · `agents/providers.py` (OpenAI/Anthropic/OpenRouter/Gemini plugáveis) · `agents/discovery.py` (SEO/crescimento).
**Dados:** users, agents, contents, tasks, logs, memories (memória compartilhada), app_settings, refresh_tokens, content_queue, agent_runs (telemetria), subscribers.
**Resiliência:** falha de agente nunca propaga; retry 2x; anti-loop 4 ciclos/h; lock de concorrência; Cost Guard corta etapas de IA sem orçamento.
**Automação 24h:** scheduler roda fila (1h) e ciclo completo (2h); ações manuais exigem autenticação administrativa.
