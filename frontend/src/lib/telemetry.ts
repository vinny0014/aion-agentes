type DataLayerItem = unknown[];

declare global {
  interface Window {
    dataLayer?: DataLayerItem[];
  }
}

let measurementId = "";
let initialized = false;
let lastPageView = "";

function safeId(value: string | undefined, pattern: RegExp): string {
  return value && pattern.test(value) ? value : "";
}

function externalScript(src: string, attributes: Record<string, string> = {}) {
  if (document.querySelector(`script[src="${src}"]`)) return;
  const script = document.createElement("script");
  script.src = src;
  script.async = true;
  Object.entries(attributes).forEach(([key, value]) => script.setAttribute(key, value));
  document.head.appendChild(script);
}

function gtag(...args: unknown[]) {
  if (!measurementId) return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(args);
}

function cleanText(value: unknown, max = 160): string {
  return String(value ?? "").replace(/[\r\n]+/g, " ").slice(0, max);
}

export function trackEvent(name: string, parameters: Record<string, unknown> = {}) {
  if (!measurementId || !/^[a-z][a-z0-9_]{1,39}$/.test(name)) return;
  gtag("event", name, parameters);
}

export function trackPageView(path: string) {
  if (!measurementId) return;
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (normalized === lastPageView) return;
  lastPageView = normalized;
  gtag("event", "page_view", {
    page_path: normalized,
    page_location: `${window.location.origin}${normalized}`,
    page_title: document.title,
  });
}

export function reportClientError(error: unknown, source = "browser") {
  trackEvent("client_error", {
    error_source: cleanText(source, 60),
    error_message: cleanText(error instanceof Error ? error.message : error),
    non_interaction: true,
  });
}

export function initializeTelemetry() {
  if (initialized) return;
  initialized = true;

  const verification = safeId(import.meta.env.VITE_GOOGLE_SITE_VERIFICATION, /^[\w-]{8,128}$/);
  if (verification && !document.querySelector('meta[name="google-site-verification"]')) {
    const meta = document.createElement("meta");
    meta.name = "google-site-verification";
    meta.content = verification;
    document.head.appendChild(meta);
  }

  measurementId = safeId(import.meta.env.VITE_GA_MEASUREMENT_ID, /^G-[A-Z0-9]{6,20}$/);
  if (measurementId) {
    externalScript(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`);
    window.dataLayer = window.dataLayer || [];
    gtag("js", new Date());
    gtag("config", measurementId, {
      anonymize_ip: true,
      send_page_view: false,
      debug_mode: import.meta.env.VITE_GA_DEBUG === "true",
    });
    window.addEventListener("error", (event) => reportClientError(event.error || event.message));
    window.addEventListener("unhandledrejection", (event) => reportClientError(event.reason, "promise"));
  }

  const ads = safeId(import.meta.env.VITE_ADSENSE_CLIENT, /^ca-pub-\d{10,20}$/);
  if (ads) {
    externalScript(
      `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(ads)}`,
      { crossorigin: "anonymous" },
    );
  }

  const cloudflare = safeId(import.meta.env.VITE_CF_ANALYTICS_TOKEN, /^[a-f0-9]{32}$/i);
  if (cloudflare) {
    externalScript("https://static.cloudflareinsights.com/beacon.min.js", {
      defer: "true",
      "data-cf-beacon": JSON.stringify({ token: cloudflare }),
    });
  }

  const clarity = safeId(import.meta.env.VITE_CLARITY_PROJECT_ID, /^[a-z0-9]{6,20}$/i);
  if (clarity) externalScript(`https://www.clarity.ms/tag/${encodeURIComponent(clarity)}`);
}
