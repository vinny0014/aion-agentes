import { SITE } from "../lib/site";
import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Nav } from "./Landing";
import AdSlot from "../lib/AdSlot";
import { API_BASE } from "../lib/api";
import { usePageMetadata } from "../lib/seo";

type Artigo = {
  id: number; title: string; slug: string; excerpt: string;
  seo_title: string; seo_description: string; published_at: string; body?: string;
  reading_time?: number; category?: string; tags?: string; image_url?: string; image_alt?: string;
  image_credit?: string; image_width?: string | number; image_height?: string | number;
  updated_at?: string; source_url?: string; author?: string;
};

function Rich({ t }: { t: string }) {
  // Suporte mínimo a **negrito** e [texto](url) — sem HTML bruto (seguro por padrão no React)
  const parts = t.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);
  return (
    <>
      {parts.map((p, i) => {
        const b = p.match(/^\*\*([^*]+)\*\*$/);
        if (b) return <strong key={i}>{b[1]}</strong>;
        const l = p.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (l && /^https?:\/\//i.test(l[2])) return <a key={i} href={l[2]} target="_blank" rel="noopener noreferrer nofollow" className="text-signal underline decoration-signal/40 hover:decoration-signal">{l[1]}</a>;
        if (l && /^\/(?!\/)/.test(l[2])) return <a key={i} href={l[2]} className="text-signal underline decoration-signal/40 hover:decoration-signal">{l[1]}</a>;
        if (l) return l[1];
        return p;
      })}
    </>
  );
}

function dataBr(iso: string | null) {
  if (!iso) return "";
  return new Date(iso.replace(" ", "T") + "Z").toLocaleDateString("en-US", {
    day: "2-digit", month: "long", year: "numeric",
  });
}

export function Conteudos() {
  usePageMetadata({
    title: "AI articles",
    description: "Browse AION's latest artificial intelligence news, guides, comparisons and analysis.",
    path: "/articles",
  });
  const [params, setParams] = useSearchParams();
  const categoria = params.get("category") || "";
  const tag = params.get("tag") || "";
  const q = params.get("q") || "";
  const [search, setBusca] = useState(q);
  const [artigos, setArtigos] = useState<Artigo[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [carregando, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const perPage = 10;

  useEffect(() => { setPage(1); }, [categoria, tag, q]);
  useEffect(() => {
    setLoading(true); setErro("");
    const u = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (categoria) u.set("category", categoria);
    if (tag) u.set("tag", tag);
    if (q) u.set("q", q);
    fetch(`${API_BASE}/api/public/articles?${u}`)
      .then((r) => { if (!r.ok) throw new Error("Articles are temporarily unavailable."); return r.json(); })
      .then((d) => { setArtigos(d.items); setTotal(d.total); })
      .catch((error: Error) => { setArtigos([]); setTotal(0); setErro(error.message); })
      .finally(() => setLoading(false));
  }, [page, categoria, tag, q]);

  const paginas = Math.max(1, Math.ceil(total / perPage));

  return (
    <div className="min-h-screen">
      <Nav />
      <main id="main-content" className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-2">daily publication</p>
        <h1 className="font-display text-4xl font-bold tracking-tight">Articles</h1>
        <form className="mt-6 flex gap-2" onSubmit={(e) => { e.preventDefault();
          const p = new URLSearchParams(params); search ? p.set("q", search) : p.delete("q"); setParams(p); }}>
          <input className="field max-w-sm" placeholder="Search articles…" value={search}
            onChange={(e) => setBusca(e.target.value)} aria-label="Search articles" />
          <button className="btn-primary !py-2">Search</button>
        </form>
        {(categoria || tag || q) && (
          <p className="mt-3 text-sm text-slateui">
            Filtering by {categoria && <>category <b className="text-ink">{categoria}</b></>}
            {tag && <>tag <b className="text-ink">{tag}</b></>}
            {q && <>search <b className="text-ink">"{q}"</b></>} ·{" "}
            <button className="text-ultra hover:underline" onClick={() => { setBusca(""); setParams({}); }}>clear</button>
          </p>
        )}
        {carregando ? (
          <div className="mt-8 space-y-6" aria-label="Loading articles">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card space-y-3">
                <div className="skeleton h-3 w-28" />
                <div className="skeleton h-6 w-3/4" />
                <div className="skeleton h-4 w-full" />
              </div>
            ))}
          </div>
        ) : erro ? (
          <p className="mt-8 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">{erro}</p>
        ) : artigos.length === 0 ? (
          <div className="empty-state mt-8">
            <span className="font-mono text-2xl text-signal">▸_</span>
            <p className="font-display font-bold text-ink">Nothing here yet</p>
            <p className="max-w-sm text-sm">Our agent team is preparing the first stories. Check back soon.</p>
          </div>
        ) : (
          <ul className="mt-8 space-y-6">
            {artigos.map((a) => (
              <li key={a.id} className="card card-hover grid gap-4 sm:grid-cols-[180px_1fr]">
                <Link to={`/article/${a.slug}`} className="block overflow-hidden rounded-lg">
                  <img src={a.image_url} alt={a.image_alt || a.title} width={1200} height={630}
                    loading="lazy" decoding="async" className="aspect-[1200/630] h-full w-full object-cover" />
                </Link>
                <div>
                  <p className="tag">{dataBr(a.published_at)}</p>
                  <Link to={`/article/${a.slug}`}
                    className="mt-1 block font-display text-xl font-bold hover:text-ultra">
                    {a.title}
                  </Link>
                  {a.excerpt && <p className="mt-2 text-sm text-slateui">{a.excerpt}</p>}
                </div>
              </li>
            ))}
          </ul>
        )}
        {paginas > 1 && (
          <nav className="mt-8 flex items-center gap-3 text-sm" aria-label="Pagination">
            <button className="btn-ghost !py-1.5" disabled={page <= 1}
              onClick={() => setPage(page - 1)}>Previous</button>
            <span className="font-mono text-xs text-slateui">{page} / {paginas}</span>
            <button className="btn-ghost !py-1.5" disabled={page >= paginas}
              onClick={() => setPage(page + 1)}>Next</button>
          </nav>
        )}
      </main>
    </div>
  );
}

export function Artigo() {
  const { slug } = useParams();
  const [artigo, setArtigo] = useState<Artigo | null>(null);
  const [relacionados, setRelacionados] = useState<Artigo[]>([]);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    setArtigo(null); setRelacionados([]); setErro(false);
    fetch(`${API_BASE}/api/public/articles/${slug}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((a: Artigo) => {
        setArtigo(a);
        // SEO dinâmico: title, description, OG e JSON-LD (Schema.org NewsArticle)
        document.title = `${a.seo_title || a.title} — AION AI NEWS OS`;
        const setMeta = (sel: string, attr: string, val: string) => {
          let el = document.querySelector(sel) as HTMLElement | null;
          if (el) el.setAttribute(attr, val);
        };
        setMeta('meta[name="description"]', "content", a.seo_description || a.excerpt || "");
        setMeta('meta[name="robots"]', "content", "index,follow,max-image-preview:large");
        setMeta('meta[property="og:type"]', "content", "article");
        setMeta('meta[property="og:title"]', "content", a.seo_title || a.title);
        setMeta('meta[property="og:description"]', "content", a.seo_description || a.excerpt || "");
        setMeta('meta[property="og:url"]', "content", `${SITE}/article/${a.slug}`);
        setMeta('meta[property="og:image"]', "content", a.image_url || `${SITE}/og-cover.png`);
        setMeta('meta[name="twitter:title"]', "content", a.seo_title || a.title);
        setMeta('meta[name="twitter:description"]', "content", a.seo_description || a.excerpt || "");
        setMeta('meta[name="twitter:image"]', "content", a.image_url || `${SITE}/og-cover.png`);
        setMeta('link[rel="canonical"]', "href", `${SITE}/article/${a.slug}`);
        setMeta('link[rel="alternate"][hreflang="en-US"]', "href", `${SITE}/article/${a.slug}`);
        setMeta('link[rel="alternate"][hreflang="x-default"]', "href", `${SITE}/article/${a.slug}`);
        const old = document.getElementById("jsonld-artigo");
        if (old) old.remove();
        const bc = document.createElement("script");
        bc.type = "application/ld+json"; bc.id = "jsonld-breadcrumb";
        document.getElementById("jsonld-breadcrumb")?.remove();
        bc.textContent = JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList",
          itemListElement:[{"@type":"ListItem",position:1,name:"Home",item:`${SITE}/`},
          {"@type":"ListItem",position:2,name:"Articles",item:`${SITE}/articles`},
          {"@type":"ListItem",position:3,name:a.title,item:`${SITE}/article/${a.slug}`}]});
        document.head.appendChild(bc);
        const ld = document.createElement("script");
        ld.type = "application/ld+json";
        ld.id = "jsonld-artigo";
        ld.textContent = JSON.stringify({
          "@context": "https://schema.org", "@type": "NewsArticle",
          headline: a.title.slice(0, 110), description: a.seo_description || a.excerpt,
          datePublished: a.published_at, dateModified: a.updated_at || a.published_at,
          inLanguage: "en-US", url: `${SITE}/article/${a.slug}`,
          mainEntityOfPage: { "@type": "WebPage", "@id": `${SITE}/article/${a.slug}` },
          articleSection: a.category || "news",
          keywords: (a.tags || "").split(",").filter(Boolean),
          ...(a.image_url ? { image: { "@type": "ImageObject", url: a.image_url,
            width: Number(a.image_width) || 1200, height: Number(a.image_height) || 630,
            caption: a.image_alt || a.title, creditText: a.image_credit || "AION Editorial" } } : {}),
          publisher: { "@type": "NewsMediaOrganization", name: "AION AI NEWS OS", url: `${SITE}/`,
            logo: { "@type": "ImageObject", url: `${SITE}/logo.png`, width: 512, height: 512 } },
          author: { "@type": "Organization", name: a.author || "AION Editorial", url: `${SITE}/about` },
        });
        document.head.appendChild(ld);
        fetch(`${API_BASE}/api/public/articles/${slug}/related`)
          .then((r) => r.json()).then(setRelacionados).catch(() => {});
      })
      .catch(() => setErro(true));
  }, [slug]);

  if (erro) {
    return (
      <div className="min-h-screen">
        <Nav />
        <main id="main-content" className="mx-auto max-w-3xl px-6 py-14">
          <h1 className="font-display text-3xl font-bold">Article not found</h1>
          <p className="mt-3 text-slateui">
            This article doesn't exist or hasn't been published yet.{" "}
            <Link to="/articles" className="text-ultra hover:underline">Browse all articles</Link>
          </p>
        </main>
      </div>
    );
  }
  if (!artigo) return <div className="p-10 font-mono text-sm text-slateui">Loading…</div>;

  return (
    <div className="min-h-screen">
      <Nav />
      <article id="main-content" className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-2">
          By {artigo.author || "AION Editorial"} · {dataBr(artigo.published_at)}
          {artigo.reading_time ? <> · {artigo.reading_time} min read</> : null}
          {artigo.category ? <> · {artigo.category}</> : null}
          {artigo.source_url ? <> · <a className="text-signal hover:underline" href={artigo.source_url} target="_blank" rel="noopener nofollow">source</a></> : null}
        </p>
        <h1 className="font-display text-4xl font-bold leading-tight tracking-tight">{artigo.title}</h1>
        {artigo.image_url && (
          <img onError={(e) => { e.currentTarget.style.display = "none"; }} src={artigo.image_url} alt={artigo.image_alt || artigo.title}
            width={1200} height={630} decoding="async" {...({ fetchpriority: "high" } as any)}
            className="mt-6 w-full rounded-xl border border-line object-cover" />
        )}
        {artigo.excerpt && <p className="mt-4 text-lg text-slateui">{artigo.excerpt}</p>}
        <div className="mt-8 space-y-4 leading-relaxed text-ink/90">
          {(artigo.body || "").split(/\n\n+/).filter(Boolean).map((p, i) => {
            if (p.startsWith("## ")) return <h2 key={i} className="pt-4 font-display text-2xl font-bold">{p.slice(3)}</h2>;
            if (p.startsWith("# ")) return <h2 key={i} className="pt-4 font-display text-2xl font-bold">{p.slice(2)}</h2>;
            return <p key={i}><Rich t={p} /></p>;
          })}
        </div>
        <AdSlot slot="aion-artigo" className="mt-8" />
        {artigo.tags && (
          <div className="mt-8 flex flex-wrap gap-2">
            {artigo.tags.split(",").filter(Boolean).map((t) => (
              <Link key={t} to={`/articles?tag=${encodeURIComponent(t)}`} className="chip !py-1 text-xs">{t}</Link>
            ))}
          </div>
        )}
        {relacionados.length > 0 && (
          <aside className="mt-12 border-t border-line pt-8" aria-label="Related articles">
            <h2 className="font-display text-xl font-bold">Related stories</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {relacionados.map((r) => (
                <Link key={r.id} to={`/article/${r.slug}`} className="card card-hover !p-3">
                  {r.image_url && <img onError={(e) => { e.currentTarget.style.display = "none"; }} src={r.image_url} alt={r.image_alt || r.title} loading="lazy"
                    className="mb-2 h-24 w-full rounded-md object-cover" />}
                  <p className="tag">{dataBr(r.published_at)}</p>
                  <p className="mt-1 text-sm font-medium leading-snug">{r.title}</p>
                </Link>
              ))}
            </div>
          </aside>
        )}
        <footer className="mt-12 border-t border-line pt-6">
          <Link to="/articles" className="text-sm font-medium text-ultra hover:underline">← All articles</Link>
        </footer>
      </article>
    </div>
  );
}
