import { useEffect } from "react";
import { SITE } from "./site";

type PageMetadata = {
  title: string;
  description: string;
  path: string;
  robots?: string;
};

function upsertMeta(selector: string, attributes: Record<string, string>) {
  let element = document.querySelector(selector) as HTMLMetaElement | null;
  if (!element) {
    element = document.createElement("meta");
    document.head.appendChild(element);
  }
  Object.entries(attributes).forEach(([name, value]) => element?.setAttribute(name, value));
}

function upsertLink(selector: string, attributes: Record<string, string>) {
  let element = document.querySelector(selector) as HTMLLinkElement | null;
  if (!element) {
    element = document.createElement("link");
    document.head.appendChild(element);
  }
  Object.entries(attributes).forEach(([name, value]) => element?.setAttribute(name, value));
}

export function usePageMetadata({ title, description, path, robots = "index,follow,max-image-preview:large" }: PageMetadata) {
  useEffect(() => {
    const canonical = `${SITE}${path === "/" ? "/" : path}`;
    const fullTitle = `${title} — AION AI NEWS OS`;
    const image = `${SITE}/og-cover.png`;
    document.title = fullTitle;
    upsertMeta('meta[name="description"]', { name: "description", content: description });
    upsertMeta('meta[name="robots"]', { name: "robots", content: robots });
    upsertMeta('meta[property="og:type"]', { property: "og:type", content: "website" });
    upsertMeta('meta[property="og:title"]', { property: "og:title", content: fullTitle });
    upsertMeta('meta[property="og:description"]', { property: "og:description", content: description });
    upsertMeta('meta[property="og:url"]', { property: "og:url", content: canonical });
    upsertMeta('meta[property="og:image"]', { property: "og:image", content: image });
    upsertMeta('meta[name="twitter:title"]', { name: "twitter:title", content: fullTitle });
    upsertMeta('meta[name="twitter:description"]', { name: "twitter:description", content: description });
    upsertMeta('meta[name="twitter:image"]', { name: "twitter:image", content: image });
    upsertLink('link[rel="canonical"]', { rel: "canonical", href: canonical });
    upsertLink('link[rel="alternate"][hreflang="en-US"]', { rel: "alternate", hreflang: "en-US", href: canonical });
    upsertLink('link[rel="alternate"][hreflang="x-default"]', { rel: "alternate", hreflang: "x-default", href: canonical });
    document.getElementById("jsonld-artigo")?.remove();
    document.getElementById("jsonld-breadcrumb")?.remove();
  }, [title, description, path, robots]);
}
