# Changelog — AION AI NEWS OS

## [1.1.0] — 2026-07-03
### Fase 2 — Portal público
- API pública paginada de artigos (`/api/public/articles`, detalhe por slug; rascunhos protegidos)
- Páginas públicas em `/articles` e `/article/:slug`, com metadados dinâmicos

### Fase 3 — Editor de conteúdo
- Editor completo no admin: criar, editar, publicar e despublicar
- Slug automático a partir do título; campos SEO com contador de 160 caracteres

### Fase 4 — Pipeline de IA
- Integração real via httpx com OpenAI, Anthropic, OpenRouter e Gemini (ativa ao configurar a key)
- Modo offline: rascunhos editoriais estruturados mantêm a publicação diária sem provedor
- Slugs únicos; falhas por item não interrompem a fila; pendências humanas registradas em log

### Fase 5 — Hardening
- Security headers (nosniff, X-Frame-Options, Referrer-Policy, HSTS em produção)
- Rate limiting por IP em login (10/min) e cadastro (5/min)
- Script de seed com artigos de demonstração

### Fase 6 — CI/CD
- GitHub Actions: testes do backend + build/typecheck do frontend em cada push/PR

## [1.0.0] — 2026-07-03
- Fundação: FastAPI + SQLite, auth JWT com refresh token rotativo, CRUDs (usuários, agentes,
  conteúdo, tarefas), logs, memória, configurações, fila + scheduler, health check,
  robots/sitemap dinâmicos, 9 agentes, frontend React/Vite/TS/Tailwind
  (landing, sobre, login, cadastro, dashboard, admin), deploy prep Vercel/Render
