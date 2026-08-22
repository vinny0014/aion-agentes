import { createReadStream, readFileSync } from "node:fs";
import { readFile, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_BACKEND = "https://aion-news-api.onrender.com";
const DEFAULT_DIST = fileURLToPath(new URL("./dist", import.meta.url));
const SEO_PATHS = new Set([
  "/robots.txt",
  "/sitemap.xml",
  "/news-sitemap.xml",
  "/image-sitemap.xml",
  "/rss.xml",
]);
const SPA_PATHS = [
  /^\/$/,
  /^\/(?:news|articles|search|categories|tags|about|privacy|terms|contact)\/?$/,
  /^\/(?:editorial-policy|corrections-policy)\/?$/,
  /^\/(?:openai|anthropic|google-ai|models|ai-agents|ai-infrastructure|robotics|business|policy|research|analysis|guides|ai-arena)\/?$/,
  /^\/ai\/(?:chatgpt|claude|gemini|llama)\/?$/,
  /^\/compare\/(?:chatgpt-vs-claude|chatgpt-vs-gemini|claude-vs-gemini)\/?$/,
  /^\/(?:login|signup|dashboard|admin)\/?$/,
  /^\/admin\/editor\/[^/]+\/?$/,
];
const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);
const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".webmanifest": "application/manifest+json",
  ".webp": "image/webp",
  ".xml": "application/xml; charset=utf-8",
};

const SITE = "https://aionnews.cloud";
const DEFAULT_METADATA = {
  title: "AION AI NEWS OS — AI news, guides and analysis",
  description: "AI news portal run by autonomous agents: daily AI Radar, guides, comparisons and analysis with sources.",
  robots: "index, follow, max-image-preview:large",
};
const ROUTE_METADATA = new Map([
  ["/", DEFAULT_METADATA],
  ["/articles", { title: "AI Articles — AION AI NEWS OS", description: "Browse AION's latest artificial intelligence news, guides, comparisons and analysis.", robots: DEFAULT_METADATA.robots }],
  ["/news", { title: "Latest AI News — AION AI NEWS OS", description: "Read the latest source-led artificial intelligence news and newsroom coverage from AION.", robots: DEFAULT_METADATA.robots }],
  ["/search", { title: "Search — AION AI NEWS OS", description: "Search AION's artificial intelligence reporting, guides and analysis.", robots: "noindex, follow" }],
  ["/analysis", { title: "AI Analysis — AION AI NEWS OS", description: "Independent analysis of the decisions, products and research shaping artificial intelligence.", robots: DEFAULT_METADATA.robots }],
  ["/guides", { title: "AI Guides — AION AI NEWS OS", description: "Practical, source-led guides to artificial intelligence models, tools and concepts.", robots: DEFAULT_METADATA.robots }],
  ["/ai-arena", { title: "AION AI Arena — Compare leading AI models", description: "Compare leading AI assistants with transparent, local-only preference voting.", robots: DEFAULT_METADATA.robots }],
  ["/ai/chatgpt", { title: "ChatGPT Guide — AION AI NEWS OS", description: "A practical guide to ChatGPT, its capabilities, limits and primary sources.", robots: DEFAULT_METADATA.robots }],
  ["/ai/claude", { title: "Claude Guide — AION AI NEWS OS", description: "A practical guide to Claude, its capabilities, limits and primary sources.", robots: DEFAULT_METADATA.robots }],
  ["/ai/gemini", { title: "Gemini Guide — AION AI NEWS OS", description: "A practical guide to Gemini, its capabilities, limits and primary sources.", robots: DEFAULT_METADATA.robots }],
  ["/ai/llama", { title: "Llama Guide — AION AI NEWS OS", description: "A practical guide to Llama, its capabilities, limits and primary sources.", robots: DEFAULT_METADATA.robots }],
  ["/compare/chatgpt-vs-claude", { title: "ChatGPT vs Claude — AION AI NEWS OS", description: "A source-led comparison of ChatGPT and Claude for real-world use.", robots: DEFAULT_METADATA.robots }],
  ["/compare/chatgpt-vs-gemini", { title: "ChatGPT vs Gemini — AION AI NEWS OS", description: "A source-led comparison of ChatGPT and Gemini for real-world use.", robots: DEFAULT_METADATA.robots }],
  ["/compare/claude-vs-gemini", { title: "Claude vs Gemini — AION AI NEWS OS", description: "A source-led comparison of Claude and Gemini for real-world use.", robots: DEFAULT_METADATA.robots }],
]);
const THIN_HUBS = new Set(["openai", "anthropic", "google-ai", "models", "ai-agents", "ai-infrastructure", "robotics", "business", "policy", "research"]);

function escapeAttribute(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function routeMetadata(pathname, statusCode) {
  const path = pathname !== "/" ? pathname.replace(/\/$/, "") : "/";
  if (ROUTE_METADATA.has(path)) return { path, ...ROUTE_METADATA.get(path) };
  const hub = path.slice(1);
  if (THIN_HUBS.has(hub)) {
    const label = hub.split("-").map((part) => part[0].toUpperCase() + part.slice(1)).join(" ");
    return { path, title: `${label} — AION AI NEWS OS`, description: `AION coverage of ${label}, with source-led reporting and analysis.`, robots: "noindex, follow" };
  }
  return {
    path,
    title: statusCode === 404 ? "Page not found — AION AI NEWS OS" : DEFAULT_METADATA.title,
    description: statusCode === 404 ? "The requested page could not be found." : DEFAULT_METADATA.description,
    robots: statusCode === 404 ? "noindex, follow" : DEFAULT_METADATA.robots,
  };
}

function replaceTag(html, pattern, replacement) {
  return pattern.test(html) ? html.replace(pattern, replacement) : html.replace("</head>", `${replacement}\n</head>`);
}

export function renderSpaHtml(source, pathname, statusCode = 200) {
  const metadata = routeMetadata(pathname, statusCode);
  const canonical = `${SITE}${metadata.path === "/" ? "/" : metadata.path}`;
  const title = escapeAttribute(metadata.title);
  const description = escapeAttribute(metadata.description);
  const robots = escapeAttribute(metadata.robots);
  const url = escapeAttribute(canonical);
  let html = replaceTag(source, /<title>[^<]*<\/title>/i, `<title>${title}</title>`);
  html = replaceTag(html, /<meta\s+name=["']description["'][^>]*>/i, `<meta name="description" content="${description}" />`);
  html = replaceTag(html, /<meta\s+name=["']robots["'][^>]*>/i, `<meta name="robots" content="${robots}" />`);
  html = replaceTag(html, /<link\s+rel=["']canonical["'][^>]*>/i, `<link rel="canonical" href="${url}" />`);
  html = replaceTag(html, /<meta\s+property=["']og:title["'][^>]*>/i, `<meta property="og:title" content="${title}" />`);
  html = replaceTag(html, /<meta\s+property=["']og:description["'][^>]*>/i, `<meta property="og:description" content="${description}" />`);
  html = replaceTag(html, /<meta\s+property=["']og:url["'][^>]*>/i, `<meta property="og:url" content="${url}" />`);
  html = replaceTag(html, /<meta\s+name=["']twitter:title["'][^>]*>/i, `<meta name="twitter:title" content="${title}" />`);
  html = replaceTag(html, /<meta\s+name=["']twitter:description["'][^>]*>/i, `<meta name="twitter:description" content="${description}" />`);
  html = html.replace(/<link\s+rel=["']alternate["']\s+hreflang=["'](?:en-US|x-default)["'][^>]*>/gi, (tag) => tag.replace(/href=["'][^"']*["']/i, `href="${url}"`));
  return html;
}

function securityHeaders(response, backendOrigin) {
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("X-Frame-Options", "DENY");
  response.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  response.setHeader(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  );
  response.setHeader(
    "Content-Security-Policy",
    "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; " +
    `form-action 'self'; img-src 'self' https: ${backendOrigin}; font-src 'self'; ` +
      "style-src 'self' 'unsafe-inline'; script-src 'self' https://www.googletagmanager.com " +
      "https://pagead2.googlesyndication.com https://static.cloudflareinsights.com https://www.clarity.ms; " +
      `connect-src 'self' ${backendOrigin} https://*.google-analytics.com ` +
      "https://*.clarity.ms https://cloudflareinsights.com https://pagead2.googlesyndication.com; " +
      "frame-src https://googleads.g.doubleclick.net https://tpc.googlesyndication.com",
  );
}

function cacheHeader(pathname) {
  if (pathname.startsWith("/assets/")) return "public, max-age=31536000, immutable";
  if (SEO_PATHS.has(pathname)) return "public, max-age=300, stale-while-revalidate=600";
  if (["/logo.png", "/og-cover.png", "/favicon.png"].includes(pathname)) {
    return "public, max-age=86400, stale-while-revalidate=604800";
  }
  return "no-cache";
}

async function bodyBuffer(request) {
  if (request.method === "GET" || request.method === "HEAD") return undefined;
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 20 * 1024 * 1024) throw new Error("Request body exceeds 20 MB");
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function proxy(request, response, target, gaMeasurementId = "") {
  try {
    const headers = {};
    for (const [name, value] of Object.entries(request.headers)) {
      if (!HOP_BY_HOP.has(name) && name !== "host" && value !== undefined) headers[name] = value;
    }
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: await bodyBuffer(request),
      redirect: "manual",
    });
    response.statusCode = upstream.status;
    for (const [name, value] of upstream.headers) {
      if (!HOP_BY_HOP.has(name) && name !== "content-encoding" && name !== "content-length") {
        response.setHeader(name, value);
      }
    }
    response.setHeader("Cache-Control", cacheHeader(new URL(target).pathname));
    const body = Buffer.from(await upstream.arrayBuffer());
    const pathname = new URL(target).pathname;
    const contentType = upstream.headers.get("content-type") || "";
    const measurementId = gaMeasurementId;
    if (pathname.startsWith("/article/") && contentType.includes("text/html") && /^G-[A-Z0-9]{6,20}$/.test(measurementId)) {
      const html = body.toString("utf8")
        .replace("</head>", `<meta name="aion-ga-measurement-id" content="${measurementId}">
<style>.aion-cookie{position:fixed;inset:0;z-index:100;display:flex;align-items:flex-end;justify-content:center;padding:16px;background:#0008}.aion-cookie[hidden]{display:none}.aion-cookie-panel{max-width:620px;border:1px solid #343044;border-radius:16px;background:#11101a;padding:20px;box-shadow:0 20px 60px #000}.aion-cookie-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.aion-cookie button{border:1px solid #5b5570;border-radius:8px;background:#221f30;color:#fff;padding:9px 13px;cursor:pointer}.aion-cookie .primary{border-color:#8b5cf6;background:#7c3aed}.aion-cookie-preferences{margin-top:14px;border:1px solid #343044;border-radius:10px;padding:12px}@media(min-width:640px){.aion-cookie{align-items:center}}</style>
<script src="/article-telemetry.js" defer></script></head>`)
        .replace("</body>", `<section id="aion-cookie-consent" class="aion-cookie" role="dialog" aria-modal="true" aria-labelledby="aion-cookie-title" hidden><div class="aion-cookie-panel"><small>PRIVACY CONTROLS</small><h2 id="aion-cookie-title">Your privacy choices</h2><p>Essential storage keeps the site working. With your permission, Google Analytics 4 measures readership and site performance. Analytics does not load before you accept.</p><div id="aion-cookie-preferences" class="aion-cookie-preferences" hidden><label><input id="aion-analytics-enabled" type="checkbox"> <strong>Analytics cookies</strong></label><p>Allow anonymized audience, article and navigation measurements.</p></div><div class="aion-cookie-actions"><button id="aion-preferences">Preferences</button><button id="aion-accept" class="primary">Accept analytics</button><button id="aion-reject">Reject analytics</button><a href="/privacy">Privacy policy</a></div></div></section></body>`);
      response.removeHeader("Content-Length");
      return response.end(html);
    }
    response.end(body);
  } catch (error) {
    response.statusCode = error.message?.includes("20 MB") ? 413 : 502;
    response.setHeader("Content-Type", "application/json; charset=utf-8");
    response.setHeader("Cache-Control", "no-store");
    response.end(JSON.stringify({ detail: "The AION backend is temporarily unavailable." }));
  }
}

async function sendFile(response, filePath, statusCode = 200) {
  try {
    const metadata = await stat(filePath);
    if (!metadata.isFile()) return false;
    response.statusCode = statusCode;
    response.setHeader("Content-Type", MIME_TYPES[extname(filePath).toLowerCase()] || "application/octet-stream");
    response.setHeader("Content-Length", metadata.size);
    response.setHeader("Cache-Control", cacheHeader(new URL(`https://local${response.req.url}`).pathname));
    if (response.req.method === "HEAD") return response.end();
    createReadStream(filePath).pipe(response);
    return true;
  } catch {
    return false;
  }
}

async function sendSpa(response, filePath, pathname, statusCode) {
  try {
    const html = renderSpaHtml(await readFile(filePath, "utf8"), pathname, statusCode);
    const body = Buffer.from(html);
    response.statusCode = statusCode;
    response.setHeader("Content-Type", "text/html; charset=utf-8");
    response.setHeader("Content-Length", body.length);
    response.setHeader("Cache-Control", "no-cache");
    if (response.req.method === "HEAD") return response.end();
    response.end(body);
    return true;
  } catch {
    return false;
  }
}

export function createAppServer({
  backendUrl = process.env.AION_BACKEND_URL || DEFAULT_BACKEND,
  distDir = process.env.AION_DIST_DIR || DEFAULT_DIST,
} = {}) {
  const backend = backendUrl.replace(/\/$/, "");
  const backendOrigin = new URL(backend).origin;
  const root = resolve(distDir);
  let builtMeasurementId = "";
  try {
    builtMeasurementId = readFileSync(join(root, "index.html"), "utf8")
      .match(/name="aion-ga-build-id" content="(G-[A-Z0-9]{6,20})"/)?.[1] || "";
  } catch {}
  const gaMeasurementId = process.env.VITE_GA_MEASUREMENT_ID || builtMeasurementId;

  return createServer(async (request, response) => {
    securityHeaders(response, backendOrigin);
    const host = (request.headers["x-forwarded-host"] || request.headers.host || "").split(":")[0];
    const protocol = request.headers["x-forwarded-proto"];
    const requestUrl = new URL(request.url || "/", `http://${request.headers.host || "localhost"}`);
    const { pathname } = requestUrl;

    if (host === "www.aionnews.cloud") {
      response.writeHead(301, { Location: `https://aionnews.cloud${requestUrl.pathname}${requestUrl.search}` });
      return response.end();
    }
    if (process.env.NODE_ENV === "production" && protocol === "http") {
      response.writeHead(301, { Location: `https://${host}${requestUrl.pathname}${requestUrl.search}` });
      return response.end();
    }
    if (pathname === "/healthz") {
      response.setHeader("Content-Type", "application/json; charset=utf-8");
      response.setHeader("Cache-Control", "no-store");
      return response.end(JSON.stringify({ status: "ok", service: "aion-news-frontend" }));
    }
    if (
      pathname === "/api" ||
      pathname.startsWith("/api/") ||
      SEO_PATHS.has(pathname) ||
      pathname.startsWith("/article/")
    ) {
      return proxy(request, response, `${backend}${requestUrl.pathname}${requestUrl.search}`, gaMeasurementId);
    }

    const requested = pathname === "/favicon.png" ? "/logo.png" : pathname;
    let decoded;
    try {
      decoded = decodeURIComponent(requested);
    } catch {
      response.statusCode = 400;
      return response.end("Bad request");
    }
    const candidate = resolve(join(root, decoded.replace(/^\/+/, "")));
    if (candidate === root || candidate.startsWith(`${root}${sep}`)) {
      if (await sendFile(response, candidate)) return;
    }

    const knownRoute = SPA_PATHS.some((pattern) => pattern.test(pathname));
    if (!extname(pathname) && await sendSpa(response, join(root, "index.html"), pathname, knownRoute ? 200 : 404)) return;
    response.statusCode = 404;
    response.setHeader("Content-Type", "text/plain; charset=utf-8");
    response.setHeader("Cache-Control", "no-store");
    response.end("Not found");
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number.parseInt(process.env.PORT || "3000", 10);
  const host = process.env.HOST || "0.0.0.0";
  createAppServer().listen(port, host, () => {
    console.log(`AION News frontend listening on ${host}:${port}`);
  });
}
