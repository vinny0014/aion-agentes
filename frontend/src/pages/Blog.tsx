import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Nav } from "./Landing";
import AdSlot from "../lib/AdSlot";

const BASE = import.meta.env.VITE_API_URL || "";

type Artigo = {
  id: number; title: string; slug: string; excerpt: string;
  seo_title: string; seo_description: string; published_at: string; body?: string;
  reading_time?: number; category?: string; tags?: string; image_url?: string; source_url?: string;
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
        if (l) return <a key={i} href={l[2]} target="_blank" rel="noopener noreferrer nofollow" className="text-signal underline decoration-signal/40 hover:decoration-signal">{l[1]}</a>;
        return p;
      })}
    </>
  );
}

function dataBr(iso: string | null) {
  if (!iso) return "";
  return new Date(iso.replace(" ", "T") + "Z").toLocaleDateString("pt-BR", {
    day: "2-digit", month: "long", year: "numeric",
  });
}

export function Conteudos() {
  const [params, setParams] = useSearchParams();
  const categoria = params.get("categoria") || "";
  const tag = params.get("tag") || "";
  const q = params.get("q") || "";
  const [busca, setBusca] = useState(q);
  const [artigos, setArtigos] = useState<Artigo[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [carregando, setCarregando] = useState(true);
  const perPage = 10;

  useEffect(() => { setPage(1); }, [categoria, tag, q]);
  useEffect(() => {
    setCarregando(true);
    const u = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (categoria) u.set("category", categoria);
    if (tag) u.set("tag", tag);
    if (q) u.set("q", q);
    fetch(`${BASE}/api/public/articles?${u}`)
      .then((r) => r.json())
      .then((d) => { setArtigos(d.items); setTotal(d.total); })
      .finally(() => setCarregando(false));
  }, [page, categoria, tag, q]);

  const paginas = Math.max(1, Math.ceil(total / perPage));

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-2">publicação diária</p>
        <h1 className="font-display text-4xl font-bold tracking-tight">Conteúdos</h1>
        <form className="mt-6 flex gap-2" onSubmit={(e) => { e.preventDefault();
          const p = new URLSearchParams(params); busca ? p.set("q", busca) : p.delete("q"); setParams(p); }}>
          <input className="field max-w-sm" placeholder="Buscar artigos…" value={busca}
            onChange={(e) => setBusca(e.target.value)} aria-label="Buscar artigos" />
          <button className="btn-primary !py-2">Buscar</button>
        </form>
        {(categoria || tag || q) && (
          <p className="mt-3 text-sm text-slateui">
            Filtrando por {categoria && <>categoria <b className="text-ink">{categoria}</b></>}
            {tag && <>tag <b className="text-ink">{tag}</b></>}
            {q && <>busca <b className="text-ink">"{q}"</b></>} ·{" "}
            <button className="text-ultra hover:underline" onClick={() => { setBusca(""); setParams({}); }}>limpar</button>
          </p>
        )}
        {carregando ? (
          <div className="mt-8 space-y-6" aria-label="Carregando artigos">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card space-y-3">
                <div className="skeleton h-3 w-28" />
                <div className="skeleton h-6 w-3/4" />
                <div className="skeleton h-4 w-full" />
              </div>
            ))}
          </div>
        ) : artigos.length === 0 ? (
          <div className="empty-state mt-8">
            <span className="font-mono text-2xl text-signal">▸_</span>
            <p className="font-display font-bold text-ink">Nada por aqui — ainda</p>
            <p className="max-w-sm text-sm">A equipe de agentes está preparando os primeiros conteúdos. Volte em breve.</p>
          </div>
        ) : (
          <ul className="mt-8 space-y-6">
            {artigos.map((a) => (
              <li key={a.id} className="card card-hover">
                <p className="tag">{dataBr(a.published_at)}</p>
                <Link to={`/conteudo/${a.slug}`}
                  className="mt-1 block font-display text-xl font-bold hover:text-ultra">
                  {a.title}
                </Link>
                {a.excerpt && <p className="mt-2 text-sm text-slateui">{a.excerpt}</p>}
              </li>
            ))}
          </ul>
        )}
        {paginas > 1 && (
          <nav className="mt-8 flex items-center gap-3 text-sm" aria-label="Paginação">
            <button className="btn-ghost !py-1.5" disabled={page <= 1}
              onClick={() => setPage(page - 1)}>Anterior</button>
            <span className="font-mono text-xs text-slateui">{page} / {paginas}</span>
            <button className="btn-ghost !py-1.5" disabled={page >= paginas}
              onClick={() => setPage(page + 1)}>Próxima</button>
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
    fetch(`${BASE}/api/public/articles/${slug}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((a: Artigo) => {
        setArtigo(a);
        // SEO dinâmico: title, description, OG e JSON-LD (Schema.org NewsArticle)
        document.title = `${a.seo_title || a.title} — AION AGENTES`;
        const setMeta = (sel: string, attr: string, val: string) => {
          let el = document.querySelector(sel) as HTMLElement | null;
          if (el) el.setAttribute(attr, val);
        };
        setMeta('meta[name="description"]', "content", a.seo_description || a.excerpt || "");
        setMeta('meta[property="og:title"]', "content", a.seo_title || a.title);
        setMeta('meta[property="og:description"]', "content", a.seo_description || a.excerpt || "");
        setMeta('meta[property="og:url"]', "content", `https://aion-agentes.vercel.app/conteudo/${a.slug}`);
        setMeta('link[rel="canonical"]', "href", `https://aion-agentes.vercel.app/conteudo/${a.slug}`);
        const old = document.getElementById("jsonld-artigo");
        if (old) old.remove();
        const bc = document.createElement("script");
        bc.type = "application/ld+json"; bc.id = "jsonld-breadcrumb";
        document.getElementById("jsonld-breadcrumb")?.remove();
        bc.textContent = JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList",
          itemListElement:[{"@type":"ListItem",position:1,name:"Home",item:"https://aion-agentes.vercel.app/"},
          {"@type":"ListItem",position:2,name:"Conteúdos",item:"https://aion-agentes.vercel.app/conteudos"},
          {"@type":"ListItem",position:3,name:a.title}]});
        document.head.appendChild(bc);
        const ld = document.createElement("script");
        ld.type = "application/ld+json";
        ld.id = "jsonld-artigo";
        ld.textContent = JSON.stringify({
          "@context": "https://schema.org", "@type": "NewsArticle",
          headline: a.title, description: a.seo_description || a.excerpt,
          datePublished: a.published_at, inLanguage: "pt-BR",
          mainEntityOfPage: `https://aion-agentes.vercel.app/conteudo/${a.slug}`,
          ...(a.image_url ? { image: [a.image_url] } : {}),
          publisher: { "@type": "Organization", name: "AION AGENTES" },
          author: { "@type": "Organization", name: "AION AGENTES" },
        });
        document.head.appendChild(ld);
        fetch(`${BASE}/api/public/articles/${slug}/related`)
          .then((r) => r.json()).then(setRelacionados).catch(() => {});
      })
      .catch(() => setErro(true));
  }, [slug]);

  if (erro) {
    return (
      <div className="min-h-screen">
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-14">
          <h1 className="font-display text-3xl font-bold">Artigo não encontrado</h1>
          <p className="mt-3 text-slateui">
            Este conteúdo não existe ou ainda não foi publicado.{" "}
            <Link to="/conteudos" className="text-ultra hover:underline">Ver todos os conteúdos</Link>
          </p>
        </main>
      </div>
    );
  }
  if (!artigo) return <div className="p-10 font-mono text-sm text-slateui">carregando…</div>;

  return (
    <div className="min-h-screen">
      <Nav />
      <article className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-2">
          Por Equipe AION · {dataBr(artigo.published_at)}
          {artigo.reading_time ? <> · {artigo.reading_time} min de leitura</> : null}
          {artigo.category ? <> · {artigo.category}</> : null}
          {artigo.source_url ? <> · <a className="text-signal hover:underline" href={artigo.source_url} target="_blank" rel="noopener nofollow">fonte</a></> : null}
        </p>
        <h1 className="font-display text-4xl font-bold leading-tight tracking-tight">{artigo.title}</h1>
        {artigo.image_url && (
          <img src={artigo.image_url} alt={`Imagem oficial: ${artigo.title}`}
            className="mt-6 w-full rounded-xl border border-line object-cover" fetchPriority="high" />
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
              <Link key={t} to={`/conteudos?tag=${encodeURIComponent(t)}`} className="chip !py-1 text-xs">{t}</Link>
            ))}
          </div>
        )}
        {relacionados.length > 0 && (
          <aside className="mt-12 border-t border-line pt-8" aria-label="Artigos relacionados">
            <h2 className="font-display text-xl font-bold">Leia também</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {relacionados.map((r) => (
                <Link key={r.id} to={`/conteudo/${r.slug}`} className="card card-hover !p-4">
                  <p className="tag">{dataBr(r.published_at)}</p>
                  <p className="mt-1 text-sm font-medium leading-snug">{r.title}</p>
                </Link>
              ))}
            </div>
          </aside>
        )}
        <footer className="mt-12 border-t border-line pt-6">
          <Link to="/conteudos" className="text-sm font-medium text-ultra hover:underline">← Todos os conteúdos</Link>
        </footer>
      </article>
    </div>
  );
}
