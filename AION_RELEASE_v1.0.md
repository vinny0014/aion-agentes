# AION AGENTES — RELEASE v1.0 (Operação OMEGA)

## Arquitetura
Monorepo com frontend SPA (React 18 + Vite 5 + TypeScript + Tailwind) e backend API REST (FastAPI + Python 3.12). Comunicação via JSON/HTTPS; auth JWT Bearer com refresh token rotativo. Scheduler interno (APScheduler) processa a fila de conteúdo a cada hora.

## Banco
SQLite com camada de acesso isolada (`core/database.py`) e migrações leves automáticas — pronto para PostgreSQL trocando a conexão. Tabelas: users, agents, contents (com category/tags), tasks, logs, memories, app_settings, refresh_tokens, content_queue.

## Backend / APIs
- Auth: register (1º usuário = admin), login, refresh rotativo, me
- CRUDs protegidos: users (admin), agents, contents, tasks
- Sistema: logs, memory (upsert por escopo), settings (recusa segredos), content-queue, pipeline/run, health
- Público (SEO/monetização): articles (paginação, busca, filtro por categoria/tag), article por slug (+reading_time), related, categories, tags, contact (rate-limited)
- Discovery: `GET /api/growth/report` (admin)
- SEO server-side: robots.txt e sitemap.xml dinâmicos

## Frontend
14 rotas: Home, Sobre, Conteúdos (busca/filtros), Artigo (JSON-LD NewsArticle, OG dinâmico, tempo de leitura, tags, relacionados), Categorias, Tags, Privacidade, Termos, Contato, Login, Cadastro, Dashboard, Admin (8 abas), Editor, 404. Design system premium: gradiente ultramarino→ciano, glass nav, glow, micro-animações com prefers-reduced-motion, skeletons, empty states.

## Agentes (10)
CEO Master, Developer, QA, Content, SEO, GitHub, Deploy, Monitor, Cost Guard e **Discovery Growth Agent** — calendário editorial, extração de palavras-chave, clusters por categoria, detecção de artigos >30 dias para atualização, e arquitetura pronta para GSC, GA4, AdSense, Trends, Bing e Cloudflare (ativam via variáveis de ambiente; nenhum resultado é garantido — o objetivo é maximizar chances).

## Fluxo de publicação diária
Tópico → fila → scheduler/`pipeline/run` → com API key: artigo por IA; sem: rascunho estruturado offline → revisão no editor → publicar → aparece no portal, sitemap e relacionados.

## SEO
Meta tags, OG, Twitter Cards, canonical, Schema.org (WebSite + NewsArticle por artigo), slugs, robots (bloqueia /admin e /dashboard), sitemap com todas as páginas públicas + artigos.

## Deploy
Vercel (frontend, `vercel.json`) + Render (backend, `render.yaml` Blueprint com disco e SECRET_KEY gerada). CI GitHub Actions.

## Roadmap / melhorias futuras
Imagens destacadas por artigo (OG image dinâmica), menu mobile hambúrguer, edição inline nos CRUDs, "esqueci minha senha" (requer e-mail transacional), PostgreSQL, RSS feed, PWA, i18n, testes E2E Playwright no CI, dark mode.
