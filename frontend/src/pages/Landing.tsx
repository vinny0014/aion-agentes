import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

const BASE = import.meta.env.VITE_API_URL || "";

import AdSlot from "../lib/AdSlot";

type Art = { id: number; title: string; slug: string; excerpt: string;
  category?: string; tags?: string; published_at: string; reading_time?: number;
  image_url?: string; image_alt?: string; breaking?: boolean };

function dataBr(iso?: string | null) {
  if (!iso) return "";
  return new Date(iso.replace(" ", "T") + "Z").toLocaleDateString("en-US",
    { day: "2-digit", month: "short", year: "numeric" });
}
function horaBr(iso?: string | null) {
  if (!iso) return "";
  return new Date(iso.replace(" ", "T") + "Z").toLocaleTimeString("en-US",
    { hour: "2-digit", minute: "2-digit" });
}

export function BottomNav() {
  const { pathname } = useLocation();
  const item = (to: string, rotulo: string, icone: string, ativo: boolean) => (
    <Link to={to} className={ativo ? "ativo" : ""}>
      <span aria-hidden className="text-base leading-none">{icone}</span>{rotulo}
    </Link>
  );
  return (
    <nav className="bottom-nav" aria-label="Bottom navigation">
      {item("/", "Home", "⌂", pathname === "/")}
      {item("/categories", "Categorias", "▤", pathname === "/categories")}
      {item("/tags", "Tags", "#", pathname === "/tags")}
      {item("/articles", "Search", "⌕", pathname.startsWith("/article"))}
      {item("/login", "Conta", "◉", pathname === "/login" || pathname === "/dashboard")}
    </nav>
  );
}

export function Nav() {
  return (
    <>
      <nav className="glass-nav">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2 font-display text-xl font-bold tracking-tight">
            <span aria-hidden className="grad-text text-2xl leading-none">▲</span>
            <span>AION<span className="block font-mono text-[9px] font-normal uppercase tracking-[0.3em] text-slateui">ai news os</span></span>
          </Link>
          <div className="hidden items-center gap-1 text-sm sm:flex">
            <Link to="/" className="px-3 py-2 text-signal">Home</Link>
            <Link to="/articles" className="px-3 py-2 text-slateui hover:text-ink">News</Link>
            <Link to="/categories" className="px-3 py-2 text-slateui hover:text-ink">Categories</Link>
            <Link to="/tags" className="px-3 py-2 text-slateui hover:text-ink">Tags</Link>
            <Link to="/about" className="px-3 py-2 text-slateui hover:text-ink">About</Link>
            <Link to="/login" className="px-3 py-2 text-slateui hover:text-ink">Sign in</Link>
            <Link to="/signup" className="btn-primary !px-4 !py-2 text-sm">Subscribe</Link>
          </div>
          <Link to="/signup" className="btn-primary !px-4 !py-2 text-sm sm:hidden">Subscribe</Link>
        </div>
      </nav>
      <BottomNav />
    </>
  );
}

function Ticker({ artigos }: { artigos: Art[] }) {
  if (artigos.length === 0) return null;
  const itens = [...artigos, ...artigos]; // loop contínuo
  return (
    <div className="overflow-hidden border-b border-line bg-surface/60">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-2.5">
        <span className="shrink-0 font-mono text-[11px] font-medium uppercase tracking-widest text-signal">⚡ Trending</span>
        <div className="relative flex-1 overflow-hidden">
          <div className="ticker-track">
            {itens.map((a, i) => (
              <Link key={i} to={`/article/${a.slug}`}
                className="shrink-0 text-sm text-slateui transition hover:text-ink">
                <span className="mr-2 text-signal">•</span>{a.title}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  const [artigos, setArtigos] = useState<Art[]>([]);
  const [tags, setTags] = useState<{ tag: string; total: number }[]>([]);
  const [email, setEmail] = useState("");
  const [newsMsg, setNewsMsg] = useState("");

  const [hero, setHero] = useState<Art | null>(null);
  useEffect(() => {
    fetch(`${BASE}/api/public/hero`).then(r => r.ok ? r.json() : null).then(setHero).catch(() => {});
    fetch(`${BASE}/api/public/articles?per_page=9`).then(r => r.json())
      .then(d => setArtigos(d.items)).catch(() => {});
    fetch(`${BASE}/api/public/tags`).then(r => r.json()).then(setTags).catch(() => {});
  }, []);

  async function assinar(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await fetch(`${BASE}/api/public/contact`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Newsletter", email, message: `Newsletter subscription: ${email}` }),
      });
      setNewsMsg(r.ok ? "Subscribed! ✓" : "Could not subscribe right now.");
      if (r.ok) setEmail("");
    } catch { setNewsMsg("Could not subscribe right now."); }
  }

  const destaque = hero || artigos[0];
  const hoje = artigos.slice(1, 5);
  const ultimas = artigos.slice(1, 5);

  const AGENTES = [
    { n: "Content", d: "Produces the portal's daily content from the queue.", r: "content" },
    { n: "SEO", d: "Optimizes titles, slugs, schema and sitemaps.", r: "optimization" },
    { n: "Discovery Growth", d: "Clusters, trends and the editorial calendar.", r: "growth" },
    { n: "QA", d: "Validates critical flows and blocks regressions.", r: "quality" },
    { n: "Cost Guard", d: "Keeps AI API spend within budget.", r: "budget" },
  ];

  return (
    <div className="min-h-screen pb-16 sm:pb-0">
      <Nav />
      <Ticker artigos={artigos.slice(0, 5)} />

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* HERO — matéria em destaque (real) */}
          <section aria-label="Featured">
            {destaque ? (
              <article className="thumb thumb-hero relative flex h-auto min-h-[380px] flex-col justify-end overflow-hidden rounded-xl border border-line p-8">
                {destaque.image_url && (
                  <img src={destaque.image_url} alt={destaque.image_alt || destaque.title}
                    width={1200} height={630}
                    className="absolute inset-0 h-full w-full object-cover opacity-45"
                    fetchPriority="high" decoding="async" />
                )}
                <div className="orb h-56 w-56 bg-ultra/40" style={{ top: "-30px", right: "6%" }} />
                <div className="relative z-10">
                  <div className="mb-4 flex flex-wrap items-center gap-2">
                    <span className="badge-feat">{destaque.breaking ? "Breaking" : "Featured"}</span>
                    <span className="font-mono text-[10px] uppercase tracking-widest text-signal">ai news</span>
                  </div>
                  <h1 className="max-w-xl font-display text-3xl font-bold leading-tight tracking-tight md:text-4xl">
                    {destaque.title}
                  </h1>
                  {destaque.excerpt && <p className="mt-3 max-w-lg text-slateui">{destaque.excerpt}</p>}
                  <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
                    <p className="font-mono text-xs text-slateui">
                      {(destaque as any).author || "AION Editorial"} · {dataBr(destaque.published_at)}
                      {destaque.reading_time ? ` · ${destaque.reading_time} min` : ""}
                    </p>
                    <Link to={`/article/${destaque.slug}`} className="btn-primary !py-2 text-sm">
                      Read story →
                    </Link>
                  </div>
                </div>
              </article>
            ) : (
              <div className="empty-state min-h-[380px] justify-center">
                <span className="font-mono text-2xl text-signal">▸_</span>
                <p className="font-display font-bold text-ink">O primeiro destaque chega em breve</p>
              </div>
            )}

            <AdSlot slot="aion-home-top" className="mt-6" />

            {/* LATEST NEWS */}
            <section className="mt-10" aria-label="Latest news">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-lg font-bold uppercase tracking-wide">Latest news</h2>
                <Link to="/articles" className="text-sm text-signal hover:underline">View all →</Link>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {ultimas.map((a) => (
                  <Link key={a.id} to={`/article/${a.slug}`} className="card card-hover !p-3">
                    <div className="thumb mb-3">
                      <img src={a.image_url} alt={a.image_alt || a.title}
                        loading="lazy" decoding="async" width={1200} height={630}
                        className="absolute inset-0 h-full w-full object-cover" />
                    </div>
                    {a.category && <p className="tag text-signal">{a.category}</p>}
                    <p className="mt-1 text-sm font-medium leading-snug">{a.title}</p>
                    <p className="mt-2 font-mono text-[11px] text-slateui">
                      {dataBr(a.published_at)}{a.reading_time ? ` · ${a.reading_time} min` : ""}
                    </p>
                  </Link>
                ))}
              </div>
            </section>

            {/* AGENT HUB */}
            <section className="mt-10" aria-label="Agent hub">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-lg font-bold uppercase tracking-wide">Agent hub</h2>
                <Link to="/about" className="text-sm text-signal hover:underline">Meet the team →</Link>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {AGENTES.map((ag) => (
                  <div key={ag.n} className="card card-hover !p-4">
                    <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg text-white"
                         style={{ backgroundImage: "var(--grad)" }} aria-hidden>▲</div>
                    <p className="font-display text-sm font-bold">{ag.n}</p>
                    <p className="mt-1 text-xs leading-snug text-slateui">{ag.d}</p>
                    <p className="tag mt-2 text-signal">{ag.r} →</p>
                  </div>
                ))}
              </div>
            </section>
          </section>

          {/* SIDEBAR */}
          <aside className="space-y-6">
            <section className="card" aria-label="Today in AI">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display font-bold uppercase tracking-wide">Today in AI</h2>
                <span className="badge-live"><span className="status-dot h-1.5 w-1.5 rounded-full bg-emerald-400" />live</span>
              </div>
              <ul className="space-y-4">
                {hoje.map((a) => (
                  <li key={a.id} className="flex gap-3">
                    <div className="thumb !h-12 !w-12 shrink-0 !rounded-md">
                      {a.image_url
                        ? <img src={a.image_url} alt={a.image_alt || a.title} loading="lazy"
                            className="absolute inset-0 h-full w-full rounded-md object-cover" />
                        : <span className="grad-text relative z-10 font-display text-sm font-bold">▲</span>}
                    </div>
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-widest text-slateui">{horaBr(a.published_at)}</p>
                      <Link to={`/article/${a.slug}`} className="text-sm font-medium leading-snug hover:text-signal">{a.title}</Link>
                    </div>
                  </li>
                ))}
                {hoje.length === 0 && <li className="text-sm text-slateui">Today's first stories are on their way.</li>}
              </ul>
              <Link to="/articles" className="btn-ghost mt-5 w-full !py-2 text-sm">View all updates →</Link>
            </section>

            <section className="card" aria-label="Newsletter">
              <h2 className="font-display font-bold uppercase tracking-wide">Newsletter</h2>
              <p className="mt-2 text-sm text-slateui">Get the best of AI, tools and analysis in your inbox.</p>
              <form onSubmit={assinar} className="mt-4 flex gap-2">
                <input className="field !py-2" type="email" required placeholder="Your email"
                  value={email} onChange={(e) => setEmail(e.target.value)} aria-label="Email para newsletter" />
                <button className="btn-primary !px-4 !py-2 text-sm">Subscribe</button>
              </form>
              {newsMsg && <p className="mt-2 text-xs text-emerald-300">{newsMsg}</p>}
              <p className="mt-2 font-mono text-[10px] text-slateui">No spam. Unsubscribe anytime.</p>
            </section>

            <AdSlot slot="aion-sidebar" />
            <section className="card" aria-label="Trending topics">
              <h2 className="font-display font-bold uppercase tracking-wide">Trending topics</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {tags.slice(0, 9).map((t) => (
                  <Link key={t.tag} to={`/articles?tag=${encodeURIComponent(t.tag)}`} className="chip !py-1 text-xs">
                    #{t.tag}
                  </Link>
                ))}
                {tags.length === 0 && <p className="text-sm text-slateui">Tags appear as articles get published.</p>}
              </div>
              <Link to="/tags" className="btn-ghost mt-5 w-full !py-2 text-sm">View all topics →</Link>
            </section>
          </aside>
        </div>
      </main>

      <div className="mx-auto max-w-6xl px-6"><AdSlot slot="aion-footer" className="mb-6" /></div>
      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-8 text-sm text-slateui">
          <span className="flex items-center gap-2 font-display font-bold text-ink">
            <span aria-hidden className="grad-text">▲</span>AION·AGENTES
          </span>
          <div className="flex gap-4 text-xs">
            <Link to="/categories" className="hover:text-ink">Categories</Link>
            <Link to="/tags" className="hover:text-ink">Tags</Link>
            <Link to="/privacy" className="hover:text-ink">Privacy</Link>
            <Link to="/terms" className="hover:text-ink">Terms</Link>
            <Link to="/contact" className="hover:text-ink">Contact</Link>
          </div>
          <span className="font-mono text-xs">© {new Date().getFullYear()} · built by agents, supervised by humans</span>
        </div>
      </footer>
    </div>
  );
}
