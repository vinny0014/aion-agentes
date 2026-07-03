# AGENTS.md — Os 16 agentes do AION

Todos executam via `run_agent()` (app/agents/core.py): isolamento de falha, retry (2x com backoff), log em `agent_runs` (entrada, saída, erro, retries, duração, tokens, custo), status na tabela `agents` e memória compartilhada (`memories`, escopo `agent:<slug>`).

| # | Agente | O que faz de verdade hoje | Limitação registrada |
|---|---|---|---|
| 1 | **CEO Master** | Orquestra o pipeline, trava concorrência, guarda anti-loop (4 ciclos/h), reinicia agentes em erro, respeita orçamento | — |
| 2 | **Discovery** | Varre fontes RSS oficiais configuráveis (OpenAI, Google, Anthropic, HF, MS, NVIDIA, arXiv, GitHub) e enfileira pautas dedupe | Rede do sandbox bloqueia as fontes; em produção funciona |
| 3 | **Content Writer** | Pipeline existente: IA (com key) ou rascunho estruturado offline | Artigo completo por IA requer API key |
| 4 | **Fact Check** | Bloqueia publicação: placeholders, corpo curto, título duplicado, links internos quebrados | Checagem factual profunda requer IA |
| 5 | **SEO** | Normaliza seo_title≤60/description≤160, gera alt-text por artigo | — |
| 6 | **Image Prompt** | Prompt original por artigo (sem marcas/pessoas/material protegido) | Geração da imagem requer API externa |
| 7 | **Translation** | Fila EN/ES registrada por artigo | Tradução requer API de IA |
| 8 | **Social Media** | Posts com texto+hashtags+CTA para 7 redes, por artigo | Publicar requer credenciais das redes |
| 9 | **Newsletter** | Tabela `subscribers`, segmentos, edição composta dos últimos artigos | Envio requer SMTP/provedor; métricas só após envios reais |
| 10 | **Analytics** | Métricas internas reais (publicados, fila, erros 24h) + recomendações | CTR/sessões/bounce exigem GA4/Cloudflare |
| 11 | **Discovery Growth** | Clusters, sugestões de categoria, palavras-chave, evergreen, artigos >30d | — |
| 12 | **AdSense Opt.** | Auditoria de conformidade + posições recomendadas; nunca práticas proibidas | Aprovação/CWV reais só em produção |
| 13 | **QA** | Valida slugs, SEO obrigatório, duplicidade; 29 testes no CI | — |
| 14 | **Security** | Audita rate limit, headers, SQLi (parametrizado), XSS (React escapa), CSRF (n/a Bearer), segredos, senhas | — |
| 15 | **Cost Guard** | Orçamento diário em settings; gasto somado de `agent_runs`; bloqueia etapas de IA ao esgotar | Custo por token só quando provedor reportar uso real |
| 16 | **Scheduler** | APScheduler: fila de conteúdo a cada 1h, ciclo completo a cada 6h, sem concorrência | — |

Pipeline (ordem): cost-guard → discovery → content → fact-check → seo → image-prompt → translation → social → newsletter → analytics → growth → adsense → qa → security.
