import { SITE } from "../lib/site";
import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Nav } from "./Landing";
import AdSlot from "../lib/AdSlot";
import { API_BASE } from "../lib/api";
import { usePageMetadata } from "../lib/seo";
import EditorialImage from "../components/EditorialImage";

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
        if (l && /^https?:\/\//i.test(l[2])) return <a key={i} href={l[2]} target="_blank" rel="noopener noreferrer" className="text-signal underline decoration-signal/40 hover:decoration-signal">{l[1]}</a>;
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
      <main id="main-content" className="mx-auto max-w-5xl px-5 py-12 sm:px-8">
        <div className="section-heading">
          <div><p className="eyebrow">AION newsroom</p><h1>Latest AI stories</h1></div>
          <p className="max-w-md text-sm leading-relaxed text-slateui">Source-led news, analysis and practical guides from across the AI industry.</p>
        </div>
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
          <ul className="mt-8 divide-y divide-line border-t border-line">
            {artigos.map((a) => (
              <li key={a.id} className="grid gap-5 py-7 sm:grid-cols-[260px_1fr]">
                <Link to={`/article/${a.slug}`} className="editorial-image block aspect-[16/10] overflow-hidden">
                  <EditorialImage src={a.image_url} alt={a.image_alt || a.title}
                    category={a.category}
                    width={a.image_width} height={a.image_height}
                    sizes="(min-width: 640px) 260px, calc(100vw - 40px)"
                    className="h-full w-full object-cover object-center" />
                </Link>
                <div className="self-center">
                  <p className="eyebrow">{a.category || "News"}</p>
                  <Link to={`/article/${a.slug}`}
                    className="mt-1 block font-display text-2xl font-bold leading-tight hover:text-signal">
                    {a.title}
                  </Link>
                  {a.excerpt && <p className="mt-2 text-sm leading-relaxed text-slateui">{a.excerpt}</p>}
                  <p className="story-meta">{dataBr(a.published_at)}{a.reading_time ? <> <span>·</span> {a.reading_time} min read</> : null}</p>
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
        setMeta('meta[property="og:image:alt"]', "content", a.image_alt || a.title);
        setMeta('meta[property="og:image:width"]', "content", String(Number(a.image_width) || 1200));
        setMeta('meta[property="og:image:height"]', "content", String(Number(a.image_height) || 630));
        setMeta('meta[name="twitter:title"]', "content", a.seo_title || a.title);
        setMeta('meta[name="twitter:description"]', "content", a.seo_description || a.excerpt || "");
        setMeta('meta[name="twitter:image"]', "content", a.image_url || `${SITE}/og-cover.png`);
        setMeta('meta[name="twitter:image:alt"]', "content", a.image_alt || a.title);
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
      <article id="main-content" className="mx-auto max-w-4xl px-5 py-12 sm:px-8 sm:py-16">
        <p className="eyebrow mb-4">{artigo.category || "AI intelligence"}</p>
        <h1 className="font-display text-4xl font-bold leading-[1.05] tracking-[-0.025em] sm:text-6xl">{artigo.title}</h1>
        {artigo.excerpt && <p className="mt-5 max-w-3xl text-xl leading-relaxed text-slateui">{artigo.excerpt}</p>}
        <div className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-line py-4 text-sm text-slateui">
          <span className="font-semibold text-ink">By {artigo.author || "AION Editorial"}</span>
          <span>·</span><time>{dataBr(artigo.published_at)}</time>
          {artigo.reading_time ? <><span>·</span><span>{artigo.reading_time} min read</span></> : null}
          {artigo.source_url ? <><span>·</span><a className="font-semibold text-signal hover:underline" href={artigo.source_url} target="_blank" rel="noopener noreferrer">Primary source ↗</a></> : null}
        </div>
        <figure className="mt-8">
          <div className="editorial-image aspect-[16/9]">
            <EditorialImage src={artigo.image_url} alt={artigo.image_alt || artigo.title}
              category={artigo.category}
              width={artigo.image_width} height={artigo.image_height} priority
              sizes="(min-width: 896px) 832px, calc(100vw - 40px)"
              className="h-full w-full object-cover object-center" />
          </div>
          {artigo.image_url && (artigo.image_credit || artigo.image_alt) && <figcaption className="mt-2 text-xs leading-relaxed text-slateui">{artigo.image_alt || artigo.title}{artigo.image_credit ? ` · ${artigo.image_credit}` : ""}</figcaption>}
        </figure>
        <div className="article-body mt-10">
          {(artigo.body || "").split(/\n\n+/).filter(Boolean).map((p, i) => <div key={i}>
            {i === 3 && <AdSlot slot="aion-artigo-inline" className="my-8" />}
            {p.startsWith("## ") || p.startsWith("# ")
              ? <h2>{p.replace(/^##? /, "")}</h2>
              : <p><Rich t={p} /></p>}
          </div>)}
        </div>
        <AdSlot slot="aion-artigo" className="mt-10" />
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
                  <EditorialImage src={r.image_url} alt={r.image_alt || r.title}
                    category={r.category}
                    width={r.image_width} height={r.image_height}
                    sizes="(min-width: 640px) 250px, calc(100vw - 64px)"
                    className="mb-2 h-24 w-full rounded-md object-cover object-center" />
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
