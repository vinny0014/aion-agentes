type DataLayerItem = IArguments | unknown[];

declare global {
  interface Window {
    dataLayer?: DataLayerItem[];
  }
}

function safeId(value: string | undefined, pattern: RegExp): string {
  return value && pattern.test(value) ? value : "";
}

function externalScript(src: string, attributes: Record<string, string> = {}) {
  const script = document.createElement("script");
  script.src = src;
  script.async = true;
  Object.entries(attributes).forEach(([key, value]) => script.setAttribute(key, value));
  document.head.appendChild(script);
}

export function initializeTelemetry() {
  const verification = safeId(import.meta.env.VITE_GOOGLE_SITE_VERIFICATION, /^[\w-]{8,128}$/);
  if (verification) {
    const meta = document.createElement("meta");
    meta.name = "google-site-verification";
    meta.content = verification;
    document.head.appendChild(meta);
  }

  const ga = safeId(import.meta.env.VITE_GA_MEASUREMENT_ID, /^G-[A-Z0-9]{6,20}$/);
  if (ga) {
    externalScript(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(ga)}`);
    window.dataLayer = window.dataLayer || [];
    const gtag = (...args: unknown[]) => window.dataLayer?.push(args);
    gtag("js", new Date());
    gtag("config", ga, { anonymize_ip: true });
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
