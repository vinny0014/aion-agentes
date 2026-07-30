import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createAppServer } from "../server.mjs";

const listen = (server) => new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const close = (server) => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));

test("Hostinger server serves the SPA and proxies API/SEO/article routes", async (t) => {
  const distDir = await mkdtemp(join(tmpdir(), "aion-hostinger-"));
  await writeFile(join(distDir, "index.html"), "<!doctype html><h1>AION SPA</h1>");
  await writeFile(join(distDir, "logo.png"), "logo");

  const backend = createServer((request, response) => {
    response.setHeader("Content-Type", request.url.endsWith(".xml") ? "application/xml" : "application/json");
    response.end(request.url.endsWith(".xml") ? "<urlset />" : JSON.stringify({ path: request.url }));
  });
  await listen(backend);
  const backendAddress = backend.address();

  const app = createAppServer({
    backendUrl: `http://127.0.0.1:${backendAddress.port}`,
    distDir,
  });
  await listen(app);
  const appAddress = app.address();
  const base = `http://127.0.0.1:${appAddress.port}`;

  t.after(async () => {
    await close(app);
    await close(backend);
    await rm(distDir, { recursive: true, force: true });
  });

  const home = await fetch(base);
  assert.equal(home.status, 200);
  assert.match(await home.text(), /AION SPA/);
  assert.equal(home.headers.get("x-content-type-options"), "nosniff");

  const articles = await fetch(`${base}/articles?q=ai`);
  assert.equal(articles.status, 200);
  assert.match(await articles.text(), /AION SPA/);

  const missing = await fetch(`${base}/does-not-exist`);
  assert.equal(missing.status, 404);
  assert.match(await missing.text(), /AION SPA/);

  const api = await fetch(`${base}/api/public/articles?per_page=1`);
  assert.equal(api.status, 200);
  assert.deepEqual(await api.json(), { path: "/api/public/articles?per_page=1" });

  const sitemap = await fetch(`${base}/sitemap.xml`);
  assert.equal(sitemap.status, 200);
  assert.equal(await sitemap.text(), "<urlset />");

  const article = await fetch(`${base}/article/example`);
  assert.equal(article.status, 200);
  assert.deepEqual(await article.json(), { path: "/article/example" });

  const health = await fetch(`${base}/healthz`);
  assert.deepEqual(await health.json(), { status: "ok", service: "aion-news-frontend" });

  const redirect = await fetch(`${base}/articles?tag=ai`, {
    headers: { "X-Forwarded-Host": "www.aionnews.cloud" },
    redirect: "manual",
  });
  assert.equal(redirect.status, 301);
  assert.equal(redirect.headers.get("location"), "https://aionnews.cloud/articles?tag=ai");
});
