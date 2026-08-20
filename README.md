# AION AI NEWS OS

Portal moderno de Inteligência Artificial com publicação diária de conteúdo, operado por uma equipe de agentes inteligentes com responsabilidades definidas.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 18 · Vite 8 · TypeScript · TailwindCSS |
| Backend | FastAPI · Python 3.12 |
| Banco | SQLite (arquitetura preparada para PostgreSQL) |
| Auth | JWT + Refresh Token com rotação · bcrypt |
| Agendador | APScheduler (pipeline de conteúdo a cada hora) |

## Estrutura

```
aion-agentes/
├── backend/
│   ├── app/
│   │   ├── main.py              # API, CORS, scheduler, robots/sitemap dinâmicos
│   │   ├── schemas.py           # Contratos Pydantic
│   │   ├── core/                # config (.env), database, security (JWT/bcrypt)
│   │   ├── routers/             # auth, CRUDs, logs, memória, settings, fila, health
│   │   └── agents/registry.py   # 35 agentes + pipeline de conteúdo plugável
│   ├── tests/test_api.py        # testes de integração e prontidão de produção
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/pages/               # Landing, Sobre, Login, Cadastro, Dashboard, Admin
│   ├── src/lib/api.ts           # Cliente com refresh automático de token
│   └── public/                  # manifest, service worker e verificação Google
├── vercel.json                  # Deploy do frontend (Vercel)
├── render.yaml                  # Deploy do backend (Render)
└── PENDENCIAS_HUMANAS.md
```

## Rodando localmente

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # edite SECRET_KEY (obrigatório)
uvicorn app.main:app --reload --port 8000
```
Documentação interativa: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev                 # proxy /api -> localhost:8000
```

### Testes
```bash
cd backend && python -m pytest tests/ -v
cd ../frontend && npm run build && npm run test:e2e
```

## Módulos

- **Landing + Institucional** — página pública com quadro de operação dos agentes
- **Auth** — cadastro, bootstrap explícito do primeiro admin com `ADMIN_SETUP_TOKEN`, login e refresh token com rotação
- **Dashboard** — status do sistema, agentes, tarefas e conteúdos
- **Painel Administrativo** — CRUD de Usuários, Agentes, Conteúdo, Tarefas + Fila, Logs, Memória e Configurações
- **Sistema de Conteúdo** — fila (`content_queue`), scheduler horário, templates e provedores plugáveis (OpenAI, Anthropic, OpenRouter, Gemini). Sem API key configurada, o pipeline cria rascunhos offline estruturados e registra a pendência em log; nada é publicado sem passar pelos gates editoriais
- **SEO** — meta tags, Open Graph, Twitter Cards, Schema.org, canonical, slugs, robots.txt e sitemap.xml dinâmico (inclui conteúdos publicados)
- **Health Check** — `GET /api/health` (status do banco, uptime, provedores configurados)
- **Portal público** — `/articles` e `/article/:slug` consomem `GET /api/public/articles` (paginada, apenas publicados)
- **Editor** — `/admin/editor/new` e `/admin/editor/:id` com slug automático, SEO e publicar/despublicar
- **Pipeline de IA** — com API key gera artigos completos; sem key gera rascunhos offline estruturados (a produção diária nunca para)
- **Seed** — `python scripts_seed.py` cria rascunhos em inglês; só publicam após receber imagem raster validada
- **CI** — GitHub Actions roda testes e build a cada push

## Documentação
ARCHITECTURE.md · AGENTS.md · API.md · DEPLOY.md · AION_RELEASE_v1.0.md · GUIA_PUBLICACAO.md · CHECKLIST_DEPLOY.md

## Agentes

CEO Master (orquestração) · Developer · QA · Content · SEO · GitHub · Deploy · Monitor · Cost Guard — registrados automaticamente no primeiro boot (`agents/registry.py`).

## Segurança

- Senhas com hash bcrypt; JWT de acesso (30 min) + refresh token (7 dias) com rotação e revogação
- Segredos **somente** em variáveis de ambiente — o endpoint de configurações **recusa** chaves com `secret/token/key/password`
- `.env` no `.gitignore`; `.env.example` versionado sem valores reais
- CORS restrito por variável de ambiente
- Security headers (nosniff, X-Frame-Options, Referrer-Policy, HSTS em produção)
- Rate limiting por IP: login 10/min, cadastro 5/min

## Deploy

**Frontend (Vercel):** domínio oficial `https://aionnews.cloud` no projeto Vercel existente. O hostname legado `aion-news-os.vercel.app` redireciona permanentemente após a ativação do DNS. Use root `frontend/`, build `npm run build` e output `dist/`. `frontend/vercel.json` encaminha API, artigos SSR, RSS e sitemaps ao backend oficial; `VITE_API_URL` pode permanecer vazio para usar o mesmo domínio.

**Backend (Render):** `https://aion-news-api.onrender.com`. O `render.yaml` cria `aion-news-api`, disco persistente, `SECRET_KEY` e `ADMIN_SETUP_TOKEN`; CORS aceita somente o frontend oficial.

## Migração para PostgreSQL

Toda a camada de acesso está isolada em `backend/app/core/database.py` com placeholders parametrizados. Para migrar: trocar a conexão sqlite3 por psycopg/SQLAlchemy e ajustar `?` → `%s`. O schema já usa tipos compatíveis.
