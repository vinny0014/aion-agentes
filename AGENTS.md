# CompraPulse — protocolo permanente de retomada

Nesta migração, leia primeiro `COMPRAPULSE_CHECKPOINT.md`. Execute `git status`,
`git branch -a`, `git log -8 --oneline` e confira o PR #22/CI antes de editar.
Continue o trabalho existente na branch `codex/comprapulse-mvp`; preserve `main`,
a produção anterior e o histórico. Não recrie o projeto nem repita entregas.
Atualize o checkpoint após cada bloco, com testes, pendências e próxima tarefa.
Continue enquanto houver trabalho seguro executável; limite de uso não encerra
o projeto. Não prometa execução em segundo plano sem scheduler comprovado.

Fase 1: SOMENTE Shopee, sem novo domínio, hospedagem ou custo fixo. Reutilize a
infraestrutura paga. Nunca invente dados comerciais, imagens ou links afiliados.
Link oficial exato, imagem real, preço/oferta recentes e status VALID são
obrigatórios. Falha/expiração retira oferta do catálogo automaticamente.
Prefira código determinístico; mantenha visita, visualização, clique, clique
atribuído, pedido, pedido aprovado e comissão aprovada separados. Lucro líquido
= comissão aprovada - Ads - custo variável. Não financiar Ads sem tracking validado.
Credenciais apenas em ambiente seguro, nunca no repositório ou logs.

Bloqueio humano real: usar HUMAN ACTION REQUIRED com WHAT, WHERE, WHY,
WHAT IS ALREADY COMPLETE e EXACT NEXT STEP; continuar tarefas independentes.

# AGENTS.md — Os 35 agentes registrados do AION (histórico preservado)

Breaking News (hero automático) · Trend Hunter (pautas de tendências) · Google Discover (auditoria de requisitos) · Image Optimization (valida imagens oficiais) · Search Console · Revenue (custo vs receita real) · Dashboard (painel executivo) · Performance. Pipeline operacional: 30 etapas.

Todos executam via `run_agent()` (app/agents/core.py): isolamento de falha, retry (2x com backoff), log em `agent_runs` (entrada, saída, erro, retries, duração, tokens, custo), status na tabela `agents` e memória compartilhada (`memories`, escopo `agent:<slug>`).

| # | Agente | O que faz de verdade hoje | Limitação registrada |
|---|---|---|---|
| 1 | **CEO Master** | Orquestra o pipeline, trava concorrência, guarda anti-loop (4 ciclos/h), reinicia agentes em erro, respeita orçamento | — |
| 2 | **Discovery** | Varre RSS de OpenAI, Google, Anthropic, Hugging Face, NVIDIA, arXiv, TechCrunch, VentureBeat, The Verge e Wired, filtrando pautas em inglês e duplicatas | Disponibilidade depende das fontes externas |
| 3 | **Content Writer** | Pipeline existente: IA (com key) ou rascunho estruturado offline | Artigo completo por IA requer API key |
| 4 | **Fact Check** | Bloqueia publicação: placeholders, corpo curto, título duplicado, links internos quebrados | Checagem factual profunda requer IA |
| 5 | **SEO** | Normaliza seo_title≤60/description≤160, gera alt-text por artigo | — |
| 6 | **Image Prompt** | Prompt original por artigo (sem marcas/pessoas/material protegido) | Geração da imagem requer API externa |
| 7 | **Language** | Audita as publicações e garante `en-US` como único idioma público | Traduções públicas permanecem desativadas |
| 8 | **Social Media** | Posts com texto+hashtags+CTA para 7 redes, por artigo | Publicar requer credenciais das redes |
| 9 | **Newsletter** | Tabela `subscribers`, segmentos, edição composta dos últimos artigos | Envio requer SMTP/provedor; métricas só após envios reais |
| 10 | **Analytics** | Métricas internas reais (publicados, fila, erros 24h) + recomendações | CTR/sessões/bounce exigem GA4/Cloudflare |
| 11 | **Discovery Growth** | Clusters, sugestões de categoria, palavras-chave, evergreen, artigos >30d | — |
| 12 | **AdSense Opt.** | Auditoria de conformidade + posições recomendadas; nunca práticas proibidas | Aprovação/CWV reais só em produção |
| 13 | **QA** | Valida slugs, SEO obrigatório, duplicidade e gates de produção; suíte de integração no CI | — |
| 14 | **Security** | Audita rate limit, headers, SQLi (parametrizado), XSS (React escapa), CSRF (n/a Bearer), segredos, senhas | — |
| 15 | **Cost Guard** | Orçamento diário em settings; gasto somado de `agent_runs`; bloqueia etapas de IA ao esgotar | Custo por token só quando provedor reportar uso real |
| 16 | **Scheduler** | APScheduler: fila de conteúdo a cada 1h, ciclo completo a cada 2h, sem concorrência | — |

Ordem crítica do pipeline: discovery → research → trend/breaking → content → SEO → image acquisition/repair/quality → fact-check → publisher. As etapas de distribuição, analytics, growth, segurança e monitoramento executam depois da publicação.
