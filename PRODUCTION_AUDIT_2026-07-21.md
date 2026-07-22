# AION production audit — 2026-07-21

## Observed production state

- Repository: `vinny0014/aion-agentes`, `main` at `2856ab1` when the audit began.
- Frontend: `https://aion-news-os.vercel.app` returned HTTP 200.
- Backend: `https://aion-news-api.onrender.com/api/health` returned `status=ok`, database `ok`, scheduler `running`, jobs `content-pipeline` and `agent-orchestrator`, release `2856ab1b2a87`.
- Content: public API reported 53 published articles. The newest entries showed repeated publication times at two-hour intervals.
- Images: the newest 50 public article image URLs all returned HTTP 200 during the audit.
- Feeds: robots, sitemap, news sitemap, image sitemap and RSS returned HTTP 200 and valid-looking XML on the legacy hostname.
- New domain: `https://aionnews.cloud` returned the Hostinger parked-domain page with `noindex`; it was not connected to Vercel.
- GA4: code accepted a Measurement ID, but production evidence for the ID, SPA page views and Realtime was unavailable.

## Root causes found

1. Canonical, RSS, sitemaps and static metadata still used the legacy Vercel hostname.
2. Redirecting the legacy hostname before DNS activation would send the live site to a parked page.
3. Discovery used exact-title deduplication only, scanned the same first four sources, did not canonicalize URLs and had no relevance, date or near-duplicate filter.
4. Provider-generated titles used `capitalize()`, damaging names such as `US`, `NVIDIA` and `OpenAI`.
5. Content generation used one body-only response and then created generic excerpts instead of receiving the editorial package in one call.
6. Image acquisition had no guaranteed local fallback; external failures could leave otherwise valid articles blocked.
7. The persistent orchestrator lock had no TTL and could remain on forever after an interrupted process.
8. Monitor only counted errors. It did not probe services, recover stuck queues, withdraw invalid publications or create incidents.
9. All Agent Hub cards reused the same triangle.
10. GA4 initialization allowed an ID but did not implement SPA navigation or required editorial events.
11. Cost events attempted to update an agent run that did not yet exist, so paid-call accounting could be attached to an older run.
12. The dashboard showed runtime state such as `idle` without a separate capability classification.

## Implemented on `codex/aion-production-final`

- Central `PUBLIC_SITE_URL` with `https://aionnews.cloud` and matching frontend metadata.
- Vercel host-based permanent redirects prepared for `www` and the legacy hostname.
- Migration CORS list covering the official domain, `www` and the legacy hostname during cutover.
- GA4 `send_page_view=false`, duplicate-safe SPA `page_view`, `article_view`, `search`, `newsletter_submit`, `login`, `sign_up` and client error events.
- Five unique inline SVG Agent Hub icons and removal of the forced blank-height block.
- Discovery URL canonicalization, English/AI relevance checks, title quality, date freshness, URL/title/slug deduplication, near-duplicate detection and official-source priority.
- One-call structured article package with title, excerpt, body, category, tags, SEO metadata and social text; official capitalization is preserved.
- Source URL persisted from the research brief; AI drafts without a valid source are blocked by Verification.
- Deterministic managed AION 1200×630 WebP template after external image fallbacks.
- Image HEAD preflight, GET streaming fallback, SSRF protection, size/type/dimension validation, retry and backoff.
- Persistent lock TTL and stale-lock recovery.
- Monitor Recovery every five minutes with service/feed probes, incident Tasks, stale content queue recovery, image retry, invalid-publication quarantine and publication-staleness detection.
- Health response extended with scheduler, queue, latest publication and last monitor report.
- Honest classifications for all 35 agent records: `OPERATIONAL`, `INTERNAL_MODULE`, `PARTIAL`, `BLOCKED_EXTERNAL`.
- Exact Cost Guard gates: economic mode at US$10, essential-only at US$12 and paid-call stop at US$13.
- Paid provider usage stored as its own auditable `agent_runs` record.

## Verification

- Backend before changes: 34/34 passed.
- Backend after changes: 40/40 passed.
- Python compilation: passed.
- Frontend TypeScript/Vite build: passed; initial bundle 61.14 kB gzip.
- Vercel JSON parsing and `git diff --check`: passed.
- Local live smoke: backend health/database/scheduler passed; jobs included `monitor-recovery`; robots and sitemap emitted `https://aionnews.cloud`.
- Local Playwright execution: blocked by the environment returning a zero-byte Chromium archive. The E2E workflow remains configured in GitHub Actions and must pass before merge.
- GitHub publication: completed on `codex/aion-production-final` through the official GitHub integration; draft PR #2 targets `main`.

## Deployment gate

Do not merge or deploy the canonical-domain changes while `aionnews.cloud` is parked. Complete `CLAUDE_BROWSER_HANDOFF.md`, confirm the domain serves AION over HTTPS, then merge, validate CI and run three production scheduler cycles.
