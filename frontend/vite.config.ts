import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";

const backend = "http://localhost:8000";
const proxy = {
  "/api": backend,
  "/robots.txt": backend,
  "/sitemap.xml": backend,
  "/news-sitemap.xml": backend,
  "/image-sitemap.xml": backend,
  "/rss.xml": backend,
};

function compraPulseHtml(html: string): string {
  return html
    .replace('<html lang="en-US">', '<html lang="pt-BR">')
    .replaceAll('AION AI NEWS OS — AI news, guides and analysis', 'CompraPulse — ofertas Shopee verificadas')
    .replace('AI news portal run by autonomous agents: daily AI Radar, guides, comparisons and analysis with sources.', 'Ofertas reais da Shopee exibidas somente após validação de preço, imagem, destino e link.')
    .replaceAll('https://aion-news-os.vercel.app/', 'https://comprapulse.aionnews.cloud/')
    .replace('content="index, follow, max-image-preview:large"', 'content="noindex, nofollow"')
    .replace(/\s*<link rel="manifest"[^>]*>/, '')
    .replaceAll('/logo.png', '/comprapulse-icon.svg')
    .replace('rel="icon" type="image/png"', 'rel="icon" type="image/svg+xml"')
    .replace(/\s*<link rel="alternate" type="application\/rss\+xml"[^>]*>/, '')
    .replace('content="#8B5CF6"', 'content="#111827"')
    .replaceAll('AION AI NEWS OS', 'CompraPulse')
    .replaceAll('Daily AI news, guides and analysis from an autonomous newsroom.', 'Ofertas Shopee verificadas antes de aparecer na vitrine.')
    .replace('content="en_US"', 'content="pt_BR"')
    .replaceAll('hreflang="en-US"', 'hreflang="pt-BR"')
    .replace(/\s*<meta property="og:image[^"]*"[^>]*>/g, '')
    .replace(/\s*<meta name="twitter:image[^"]*"[^>]*>/g, '')
    .replace('"inLanguage": "en-US"', '"inLanguage": "pt-BR"')
    .replace('"@type": "NewsMediaOrganization"', '"@type": "Organization"')
    .replaceAll('https://comprapulse.aionnews.cloud/articles?q={search_term_string}', 'https://comprapulse.aionnews.cloud/?q={search_term_string}');
}

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    ...(mode === 'comprapulse' ? [{
      name: 'comprapulse-standalone-html',
      transformIndexHtml: compraPulseHtml,
      generateBundle() {
        this.emitFile({
          type: 'asset',
          fileName: '.htaccess',
          source: readFileSync(new URL('./deploy/comprapulse.htaccess', import.meta.url), 'utf8'),
        });
      },
    }] : []),
  ],
  server: { proxy },
  preview: { proxy },
}));
