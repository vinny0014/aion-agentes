# API.md — principais endpoints (docs interativas em /docs)
**Público:** GET /api/public/articles [?q,category,tag,page] · /articles/{slug} (+reading_time) · /articles/{slug}/related · /categories · /tags · POST /contact · POST /newsletter · GET /api/health · /robots.txt · /sitemap.xml
**Auth:** POST /api/auth/register|login|refresh · GET /me
**Protegido:** CRUDs /api/users(admin)/agents/contents/tasks · /api/logs(admin) · /api/memory · /api/settings(admin) · /api/content-queue · POST /api/pipeline/run
**Multiagente (admin):** POST /api/orchestrator/run · GET /api/orchestrator/runs[?agent] · GET /api/orchestrator/metrics · GET /api/growth/report
