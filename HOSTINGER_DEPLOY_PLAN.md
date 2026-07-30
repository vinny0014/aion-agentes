# AION News — Hostinger deployment

This branch prepares the existing Vite frontend for Hostinger without replacing
the Render backend or the Vercel rollback.

## Web App settings

- Repository: `vinny0014/aion-agentes`
- Branch: `codex/aion-production-final`
- Root directory: `frontend`
- Framework: `Other` (Node.js) or the detected Vite application with an entry file
- Node.js: `22.x`
- Install: `npm ci`
- Build: `npm run build`
- Output directory: `dist`
- Entry file: `server.mjs`
- Start: `npm start`
- Health path: `/healthz`

The Node entry point serves the Vite build, preserves real 404 responses, redirects
`www` to the apex domain, and proxies `/api`, article HTML, robots, sitemaps and RSS
to the existing Render service. No frontend secret is required.

Optional environment variables:

- `AION_BACKEND_URL=https://aion-news-api.onrender.com`
- `VITE_GA_MEASUREMENT_ID` (AION News property only)
- `VITE_GOOGLE_SITE_VERIFICATION`
- `VITE_ADSENSE_CLIENT`
- `VITE_CF_ANALYTICS_TOKEN`
- `VITE_CLARITY_PROJECT_ID`

Do not copy credentials or analytics IDs from AION Crypto.

## Safe activation order

1. Deploy this branch to a temporary Hostinger URL.
2. Validate `/`, `/articles`, one `/article/<slug>`, `/api/public/articles`,
   `/robots.txt`, the three sitemaps, `/rss.xml`, `/healthz`, and a real 404.
3. Add `https://aionnews.cloud` and `https://www.aionnews.cloud` to the Render
   `CORS_ORIGINS` value while retaining `https://aion-news-os.vercel.app`.
4. Set the Render `PUBLIC_SITE_URL` to `https://aionnews.cloud` only when the
   Hostinger preview is approved and the domain cutover is authorized.
5. Change only the AION News DNS records after the exact authorization requested
   in the migration plan.
6. Validate HTTPS, apex, `www` 301, API, article HTML, robots, sitemaps and RSS.
7. Enable indexation and submit the sitemaps only after the final production checks.

Vercel must remain available until the Hostinger deployment has passed the
stability checks. Do not merge this PR as part of the preparation step.
