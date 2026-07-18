# API.md — principais endpoints (docs interativas em /docs)
**Público:** `GET /api/public/articles` (`q`, `category`, `tag`, `page`) · `/articles/{slug}` · `/articles/{slug}/related` · `/categories` · `/tags` · imagens persistidas em `/images/{filename}` · `POST /contact` · `POST /newsletter` · `GET /api/health`.

**SEO público:** `GET /article/{slug}` (HTML server-rendered) · `/robots.txt` · `/sitemap.xml` · `/news-sitemap.xml` · `/image-sitemap.xml` · `/rss.xml` · `/favicon.png` · `/icon-192.png` · `/icon-512.png` · `/og-cover.png`.

**Auth:** `POST /api/auth/register` (o primeiro admin exige `setup_token`) · `/login` · `/refresh` · `GET /me`.

**Protegido:** CRUDs `/api/users` (admin), `/agents`, `/contents` (escrita admin) e `/tasks` · `/api/logs` (admin) · `/api/memory` · `/api/settings` (admin) · `/api/content-queue` · `POST /api/pipeline/run` (admin).

**Multiagente (admin):** `POST /api/orchestrator/run` · `GET /api/orchestrator/runs` · `/metrics` · `/health/google` · `POST /cover` · `POST /upload-image` · `GET /api/growth/report`.
