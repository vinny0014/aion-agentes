type DataLayerItem = unknown[];

declare global {
  interface Window {
    dataLayer?: DataLayerItem[];
  }
}

let measurementId = "";
let initialized = false;
let lastPageView = "";
let analyticsLoaded = false;
const sentOnce = new Set<string>();

export const CONSENT_STORAGE_KEY = "aion_cookie_consent_v1";
export const CONSENT_EVENT = "aion:consent-updated";
export type AnalyticsConsent = "granted" | "denied" | null;

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
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(args);
}

export function getAnalyticsConsent(): AnalyticsConsent {
  try {
    const value = window.localStorage.getItem(CONSENT_STORAGE_KEY);
    return value === "granted" || value === "denied" ? value : null;
  } catch {
    return null;
  }
}

export function setAnalyticsConsent(consent: Exclude<AnalyticsConsent, null>) {
  try { window.localStorage.setItem(CONSENT_STORAGE_KEY, consent); } catch {}
  gtag("consent", "update", { analytics_storage: consent });
  if (consent === "granted") loadAnalytics();
  window.dispatchEvent(new CustomEvent(CONSENT_EVENT, { detail: { analytics: consent } }));
}

export function openCookiePreferences() {
  window.dispatchEvent(new Event("aion:open-cookie-preferences"));
}

function cleanText(value: unknown, max = 160): string {
  return String(value ?? "").replace(/[\r\n]+/g, " ").slice(0, max);
}

export function trackEvent(name: string, parameters: Record<string, unknown> = {}) {
  if (!analyticsLoaded || getAnalyticsConsent() !== "granted" || !/^[a-z][a-z0-9_]{1,39}$/.test(name)) return;
  gtag("event", name, parameters);
}

export function trackEventOnce(name: string, key: string, parameters: Record<string, unknown> = {}) {
  if (!analyticsLoaded || getAnalyticsConsent() !== "granted") return;
  const eventKey = `${name}:${key}`;
  if (sentOnce.has(eventKey)) return;
  sentOnce.add(eventKey);
  trackEvent(name, parameters);
}

export function trackPageView(path: string) {
  if (!analyticsLoaded || getAnalyticsConsent() !== "granted") return;
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
  window.dataLayer = window.dataLayer || [];
  gtag("consent", "default", {
    analytics_storage: getAnalyticsConsent() === "granted" ? "granted" : "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    wait_for_update: 500,
  });
  if (getAnalyticsConsent() === "granted") loadAnalytics();
}

function loadAnalytics() {
  if (!measurementId || analyticsLoaded || getAnalyticsConsent() !== "granted") return;
  analyticsLoaded = true;
  externalScript(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`);
  gtag("js", new Date());
  gtag("config", measurementId, {
    anonymize_ip: true,
    send_page_view: false,
    debug_mode: import.meta.env.VITE_GA_DEBUG === "true",
  });
  window.addEventListener("error", (event) => reportClientError(event.error || event.message));
  window.addEventListener("unhandledrejection", (event) => reportClientError(event.reason, "promise"));
}
