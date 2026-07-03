import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Nav } from "./Landing";

const BASE = import.meta.env.VITE_API_URL || "";

type Artigo = {
  id: number; title: string; slug: string; excerpt: string;
  seo_title: string; seo_description: string; published_at: string; body?: string;
};

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
          <p className="mt-8 font-mono text-sm text-slateui">carregando…</p>
        ) : artigos.length === 0 ? (
          <p className="mt-8 text-slateui">
            Ainda não há artigos publicados. A equipe de agentes está preparando os primeiros conteúdos.
          </p>
        ) : (
          <ul className="mt-8 space-y-6">
            {artigos.map((a) => (
              <li key={a.id} className="card">
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
  const [erro, setErro] = useState(false);

  useEffect(() => {
    fetch(`${BASE}/api/public/articles/${slug}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((a: Artigo) => {
        setArtigo(a);
        document.title = `${a.seo_title || a.title} — AION AGENTES`;
        const m = document.querySelector('meta[name="description"]');
        if (m) m.setAttribute("content", a.seo_description || a.excerpt || "");
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
        <p className="tag mb-2">{dataBr(artigo.published_at)}</p>
        <h1 className="font-display text-4xl font-bold leading-tight tracking-tight">{artigo.title}</h1>
        {artigo.excerpt && <p className="mt-4 text-lg text-slateui">{artigo.excerpt}</p>}
        <div className="mt-8 space-y-4 leading-relaxed text-ink/90">
          {(artigo.body || "").split(/\n\n+/).filter(Boolean).map((p, i) => {
            if (p.startsWith("## ")) return <h2 key={i} className="pt-4 font-display text-2xl font-bold">{p.slice(3)}</h2>;
            if (p.startsWith("# ")) return <h2 key={i} className="pt-4 font-display text-2xl font-bold">{p.slice(2)}</h2>;
            return <p key={i}>{p}</p>;
          })}
        </div>
        <footer className="mt-12 border-t border-ink/10 pt-6">
          <Link to="/conteudos" className="text-sm font-medium text-ultra hover:underline">← Todos os conteúdos</Link>
        </footer>
      </article>
    </div>
  );
}
