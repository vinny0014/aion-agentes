# Claude Browser handoff — external-only actions

Claude must not edit repository code. It may perform only the authenticated browser steps below. Never paste passwords, tokens or recovery codes into chat, screenshots, Issues or logs.

## 1. Connect the domain in Vercel

- Service: Vercel.
- URL: open the existing AION project, then **Settings → Domains**.
- Login: required; use the owner's existing session.
- Objective: add `aionnews.cloud` and `www.aionnews.cloud` to the existing project that currently serves `aion-news-os.vercel.app`.
- Exact action: add both domains; set `aionnews.cloud` as primary; copy the exact DNS records Vercel displays. Do not guess record values.
- Validate: Vercel must show both domains as correctly configured. Do not enable the legacy-host redirect until the apex domain serves AION.
- Screenshot expected: Domains page showing apex and `www`, project name visible, secrets hidden.
- Risk: adding the domain is safe; changing unrelated project settings is not authorized.
- Return to Work: exact DNS record type/name/value requested by Vercel and configuration status.

## 2. Replace Hostinger parked DNS

- Service: Hostinger DNS Zone Editor.
- URL: Hostinger control panel for `aionnews.cloud`.
- Login: required.
- Objective: point apex and `www` to the Vercel project.
- Exact action: remove only the parking records that conflict with the Vercel instructions; create exactly the records copied from Vercel; preserve MX, TXT and unrelated records.
- Validate: wait for Vercel to report valid DNS and SSL. Open `https://aionnews.cloud` and confirm the AION homepage, not “Parked Domain”. Open `https://www.aionnews.cloud` and confirm it redirects to the apex.
- Screenshot expected: DNS rows with sensitive values hidden where appropriate, Vercel valid-domain status, and AION homepage under the apex hostname.
- Risk: deleting unrelated DNS can break email. Touch only conflicting apex/`www` web records.
- Return to Work: confirmation of apex response, `www` redirect and SSL.

## 3. Configure production environment values

- Service: Vercel project settings.
- Fields:
  - `VITE_SITE_URL=https://aionnews.cloud`
  - `VITE_GA_MEASUREMENT_ID=<real GA4 ID from step 4>`
  - `VITE_GOOGLE_SITE_VERIFICATION=<real Search Console token from step 5>` when supplied.
- Service: Render `aion-news-api` environment.
- Fields:
  - `PUBLIC_SITE_URL=https://aionnews.cloud`
  - `CORS_ORIGINS=https://aionnews.cloud,https://www.aionnews.cloud,https://aion-news-os.vercel.app`
- Secrets: preserve existing `SECRET_KEY`, `ADMIN_SETUP_TOKEN`, `OPENAI_API_KEY` and all other values. Do not reveal or rotate them.
- Validate: environment variable names are present; values are not shown in screenshots. Redeploy only after the code PR is approved for merge.
- Return to Work: which variables were added/updated and which service needs redeploy.

## 4. Create or connect GA4

- Service: Google Analytics.
- URL: Analytics Admin for the owner's account.
- Objective: create or reuse one GA4 web data stream for `https://aionnews.cloud`.
- Exact action: copy the real Measurement ID beginning with `G-`; save it as Vercel `VITE_GA_MEASUREMENT_ID`; redeploy after merge.
- Validate: GA4 Realtime/DebugView must receive one SPA `page_view` per route and the events `article_view`, `search` and `newsletter_submit`. Confirm that route navigation does not double-count page views.
- Screenshot expected: stream name and Measurement ID (the ID may be returned to Work), plus Realtime/DebugView event names without personal visitor data.
- Risk: do not create duplicate properties if an AION property already exists.
- Return to Work: Measurement ID and observed event names.

## 5. Verify Google Search Console

- Service: Google Search Console.
- Objective: create/verify the Domain property `aionnews.cloud` or the URL-prefix property `https://aionnews.cloud/` using Google's exact instructions.
- Exact action: if DNS TXT verification is requested, copy the exact TXT value to Hostinger without altering other TXT records. Submit:
  - `https://aionnews.cloud/sitemap.xml`
  - `https://aionnews.cloud/news-sitemap.xml`
  - `https://aionnews.cloud/image-sitemap.xml`
- Validate: property verified; each sitemap accepted or processing; inspect the homepage and one article URL.
- Screenshot expected: verified property and sitemap status.
- Return to Work: verification method, sitemap statuses and inspected URL result.

## 6. Verify Bing Webmaster Tools

- Service: Bing Webmaster Tools.
- Objective: import the verified Search Console property when available, or use Bing's exact verification method.
- Exact action: submit `https://aionnews.cloud/sitemap.xml`; copy any IndexNow key only if Bing supplies one and no paid plan is required.
- Validate: site verified and sitemap accepted/processing.
- Screenshot expected: site and sitemap status.
- Return to Work: verification and sitemap result; IndexNow key only through the protected secret workflow.

## 7. Final post-merge validation

- Merge condition: GitHub CI is green and steps 1–3 are complete.
- Validate these URLs:
  - `https://aionnews.cloud/`
  - `https://aionnews.cloud/api/health`
  - `https://aionnews.cloud/robots.txt`
  - `https://aionnews.cloud/sitemap.xml`
  - `https://aionnews.cloud/news-sitemap.xml`
  - `https://aionnews.cloud/image-sitemap.xml`
  - `https://aionnews.cloud/rss.xml`
  - one current article and its image.
- Redirects:
  - `https://www.aionnews.cloud/...` → same path on apex.
  - `https://aion-news-os.vercel.app/...` → same path on apex.
- Required evidence: HTTP status/final URL, apex canonical in HTML/XML, GA4 Realtime events, backend release SHA, monitor report and three consecutive scheduler publication cycles.
- Task status: only after evidence, change the five existing Admin Tasks from `todo` to `done`. Leave GA4/domain Tasks blocked if external configuration is incomplete.
