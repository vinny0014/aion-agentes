import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { API_BASE } from "../lib/api";
import { usePageMetadata } from "../lib/seo";
import AdSlot from "../lib/AdSlot";

type Art = {
  id: number; title: string; slug: string; excerpt: string; category?: string;
  tags?: string; published_at: string; reading_time?: number; image_url?: string;
  image_alt?: string; image_credit?: string; breaking?: boolean; author?: string;
};

function formatDate(iso?: string | null) {
  if (!iso) return "";
  return new Date(iso.replace(" ", "T") + "Z").toLocaleDateString("en-US", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function StoryImage({ story, className = "", eager = false }: { story: Art; className?: string; eager?: boolean }) {
  return (
    <div className={`editorial-image ${className}`}>
      {story.image_url ? (
        <img src={story.image_url} alt={story.image_alt || story.title} width={1200} height={630}
          loading={eager ? "eager" : "lazy"} decoding="async"
          {...(eager ? ({ fetchpriority: "high" } as any) : {})}
          onError={(event) => { event.currentTarget.style.display = "none"; }}
          className="h-full w-full object-cover" />
      ) : <div className="flex h-full items-center justify-center bg-surface text-4xl font-bold text-signal">A</div>}
    </div>
  );
}

function Meta({ story, showAuthor = false }: { story: Art; showAuthor?: boolean }) {
  return <p className="story-meta">
    {showAuthor && <>{story.author || "AION Editorial"}<span>·</span></>}
    {formatDate(story.published_at)}
    {story.reading_time ? <><span>·</span>{story.reading_time} min read</> : null}
  </p>;
}

export function BottomNav() {
  const { pathname } = useLocation();
  const item = (to: string, label: string, icon: string, active: boolean) => (
    <Link to={to} className={active ? "ativo" : ""} aria-current={active ? "page" : undefined}>
      <span aria-hidden className="text-base leading-none">{icon}</span>{label}
    </Link>
  );
  return <nav className="bottom-nav" aria-label="Bottom navigation">
    {item("/", "Home", "⌂", pathname === "/")}
    {item("/articles", "News", "▤", pathname.startsWith("/article"))}
    {item("/categories", "Topics", "#", pathname === "/categories")}
    {item("/about", "About", "A", pathname === "/about")}
    {item("/login", "Account", "◉", pathname === "/login" || pathname === "/dashboard")}
  </nav>;
}

export function Nav() {
  return <>
    <a href="#main-content" className="skip-link">Skip to main content</a>
    <header className="site-header">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="flex items-center justify-between border-b border-line py-4">
          <Link to="/" className="brand-lockup" aria-label="AION AI News home">
            <span className="brand-mark" aria-hidden>A</span>
            <span><strong>AION</strong><small>AI NEWS</small></span>
          </Link>
          <p className="hidden text-xs text-slateui lg:block">Independent intelligence for the AI economy</p>
          <div className="flex items-center gap-3">
            <Link to="/login" className="hidden text-sm text-slateui hover:text-ink sm:inline">Sign in</Link>
            <a href="/#newsletter" className="btn-primary !px-4 !py-2 text-sm">Get the briefing</a>
          </div>
        </div>
        <nav className="hidden items-center gap-6 overflow-x-auto py-3 text-sm sm:flex" aria-label="Primary navigation">
          <Link to="/" className="font-semibold text-ink">Top stories</Link>
          <Link to="/articles" className="text-slateui hover:text-ink">Latest</Link>
          <Link to="/articles?category=analysis" className="text-slateui hover:text-ink">Analysis</Link>
          <Link to="/articles?category=guides" className="text-slateui hover:text-ink">Guides</Link>
          <Link to="/articles?tag=agents" className="text-slateui hover:text-ink">AI agents</Link>
          <Link to="/articles?tag=openai" className="text-slateui hover:text-ink">OpenAI</Link>
          <Link to="/categories" className="text-slateui hover:text-ink">All topics</Link>
          <Link to="/about" className="ml-auto text-slateui hover:text-ink">About AION</Link>
        </nav>
      </div>
    </header>
    <BottomNav />
  </>;
}

async function readJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

function NewsTicker({ stories, loading }: { stories: Art[]; loading: boolean }) {
  return <div className="border-b border-line bg-surface/50">
    <div className="mx-auto flex min-h-11 max-w-7xl items-center gap-4 px-5 sm:px-8">
      <span className="shrink-0 text-[11px] font-bold uppercase tracking-[0.18em] text-signal">News wire</span>
      <div className="min-w-0 flex-1 overflow-hidden">
        {loading ? <div className="skeleton h-4 max-w-lg" aria-hidden /> : stories.length ? (
          <div className="ticker-track">{[...stories, ...stories].map((story, index) => (
            <Link key={`${story.id}-${index}`} to={`/article/${story.slug}`} className="shrink-0 text-sm text-slateui hover:text-ink">
              <span className="mr-2 text-signal">●</span>{story.title}
            </Link>
          ))}</div>
        ) : <p className="text-sm text-slateui">The newsroom is preparing the next briefing.</p>}
      </div>
    </div>
  </div>;
}

export default function Landing() {
  usePageMetadata({
    title: "AI news, analysis and practical intelligence",
    description: "Independent AI news, source-led analysis and practical guides for people building and using artificial intelligence.",
    path: "/",
  });
  const [articles, setArticles] = useState<Art[]>([]);
  const [tags, setTags] = useState<{ tag: string; total: number }[]>([]);
  const [hero, setHero] = useState<Art | null>(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [newsletterMessage, setNewsletterMessage] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.allSettled([
      readJson<Art | null>("/api/public/hero", controller.signal),
      readJson<{ items: Art[] }>("/api/public/articles?per_page=12", controller.signal),
      readJson<{ tag: string; total: number }[]>("/api/public/tags", controller.signal),
    ]).then(([heroResult, articleResult, tagResult]) => {
      if (controller.signal.aborted) return;
      if (heroResult.status === "fulfilled") setHero(heroResult.value);
      if (articleResult.status === "fulfilled") setArticles(articleResult.value.items);
      if (tagResult.status === "fulfilled") setTags(tagResult.value);
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  async function subscribe(event: React.FormEvent) {
    event.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/api/public/newsletter`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }),
      });
      setNewsletterMessage(response.ok ? "You're on the list." : "Could not subscribe right now.");
      if (response.ok) setEmail("");
    } catch { setNewsletterMessage("Could not subscribe right now."); }
  }

  const featured = hero || articles[0];
  const withoutFeatured = useMemo(() => articles.filter((article) => article.id !== featured?.id), [articles, featured]);
  const leadStories = withoutFeatured.slice(0, 2);
  const latest = withoutFeatured.slice(2, 8);

  return <div className="min-h-screen pb-16 sm:pb-0">
    <Nav />
    <NewsTicker stories={articles.slice(0, 6)} loading={loading} />

    <main id="main-content" className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-12" aria-busy={loading}>
      <section aria-labelledby="top-stories-heading">
        <div className="section-heading">
          <div><p className="eyebrow">AION Daily</p><h1 id="top-stories-heading">The intelligence that matters now</h1></div>
          <p className="max-w-md text-sm leading-relaxed text-slateui">Source-led reporting and practical analysis of models, agents, products, policy and the companies shaping AI.</p>
        </div>
        {loading ? (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.75fr)_minmax(280px,.75fr)]">
            <div className="skeleton aspect-[16/10]" /><div className="space-y-6"><div className="skeleton h-64" /><div className="skeleton h-64" /></div>
          </div>
        ) : featured ? (
          <div className="grid gap-7 lg:grid-cols-[minmax(0,1.75fr)_minmax(280px,.75fr)]">
            <article>
              <Link to={`/article/${featured.slug}`} className="block"><StoryImage story={featured} eager className="aspect-[16/9]" /></Link>
              <div className="pt-5">
                <p className="eyebrow">{featured.breaking ? "Breaking" : featured.category || "Featured"}</p>
                <Link to={`/article/${featured.slug}`}><h2 className="mt-2 font-display text-4xl font-bold leading-[1.04] tracking-[-0.025em] hover:text-signal md:text-5xl">{featured.title}</h2></Link>
                {featured.excerpt && <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slateui">{featured.excerpt}</p>}
                <Meta story={featured} showAuthor />
              </div>
            </article>
            <div className="divide-y divide-line border-y border-line">
              {leadStories.map((story) => <article key={story.id} className="py-5 first:pt-0">
                <Link to={`/article/${story.slug}`}><StoryImage story={story} className="aspect-[16/9]" /></Link>
                <p className="eyebrow mt-4">{story.category || "News"}</p>
                <Link to={`/article/${story.slug}`}><h2 className="mt-1 font-display text-2xl font-bold leading-tight hover:text-signal">{story.title}</h2></Link>
                <Meta story={story} />
              </article>)}
            </div>
          </div>
        ) : <div className="empty-state"><p className="font-display text-2xl font-bold">The next AION briefing is being prepared.</p></div>}
      </section>

      <AdSlot slot="aion-home-top" className="my-10" />

      <div className="mt-14 grid gap-12 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section aria-labelledby="latest-heading">
          <div className="section-heading !mb-6">
            <div><p className="eyebrow">Newsroom</p><h2 id="latest-heading">Latest stories</h2></div>
            <Link to="/articles" className="text-sm font-semibold text-signal hover:underline">See all stories →</Link>
          </div>
          <div className="divide-y divide-line border-t border-line">
            {latest.map((story) => <article key={story.id} className="grid gap-5 py-6 sm:grid-cols-[220px_1fr]">
              <Link to={`/article/${story.slug}`}><StoryImage story={story} className="aspect-[16/10]" /></Link>
              <div className="self-center">
                <p className="eyebrow">{story.category || "News"}</p>
                <Link to={`/article/${story.slug}`}><h3 className="mt-1 font-display text-2xl font-bold leading-tight hover:text-signal">{story.title}</h3></Link>
                {story.excerpt && <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-slateui">{story.excerpt}</p>}
                <Meta story={story} />
              </div>
            </article>)}
          </div>
        </section>

        <aside className="space-y-8">
          <section id="newsletter" className="newsletter-panel scroll-mt-24" aria-labelledby="newsletter-heading">
            <p className="eyebrow !text-white/70">The AION Brief</p>
            <h2 id="newsletter-heading" className="mt-2 font-display text-3xl font-bold">One useful AI briefing. No hype.</h2>
            <p className="mt-3 text-sm leading-relaxed text-white/70">The most important developments, what they mean, and what to watch next.</p>
            <form onSubmit={subscribe} className="mt-5 space-y-3">
              <input className="field !border-white/20 !bg-black/20 !text-white placeholder:!text-white/50" type="email" required placeholder="you@example.com" value={email} onChange={(event) => setEmail(event.target.value)} aria-label="Newsletter email" />
              <button className="w-full rounded-md bg-white px-4 py-2.5 text-sm font-bold text-black hover:bg-white/90">Join the briefing</button>
            </form>
            {newsletterMessage && <p className="mt-3 text-xs text-white" aria-live="polite">{newsletterMessage}</p>}
            <p className="mt-3 text-[11px] text-white/55">Free. No spam. Unsubscribe anytime.</p>
          </section>
          <section className="border-t border-line pt-6" aria-labelledby="topics-heading">
            <div className="flex items-center justify-between"><h2 id="topics-heading" className="font-display text-2xl font-bold">Topics to follow</h2><Link to="/tags" className="text-xs text-signal">All topics</Link></div>
            <div className="mt-4 flex flex-wrap gap-2">{tags.slice(0, 10).map((item) => <Link key={item.tag} to={`/articles?tag=${encodeURIComponent(item.tag)}`} className="chip !py-1 text-xs">{item.tag}</Link>)}</div>
          </section>
          <section className="border-t border-line pt-6" aria-labelledby="standards-heading">
            <p className="eyebrow">Why trust AION</p><h2 id="standards-heading" className="mt-2 font-display text-2xl font-bold">Sources before speed</h2>
            <p className="mt-3 text-sm leading-relaxed text-slateui">Every publishable story must include attributable sourcing, a useful original angle and a verified editorial image.</p>
            <div className="mt-4 flex gap-4 text-xs font-semibold"><Link to="/editorial-policy" className="text-signal hover:underline">Editorial policy</Link><Link to="/corrections-policy" className="text-signal hover:underline">Corrections</Link></div>
          </section>
          <AdSlot slot="aion-sidebar" />
        </aside>
      </div>

      <section className="mt-16 border-y border-line py-10" aria-labelledby="start-heading">
        <p className="eyebrow">Start here</p>
        <div className="mt-2 grid gap-8 md:grid-cols-[1fr_2fr]">
          <h2 id="start-heading" className="font-display text-3xl font-bold">Follow AI by the question you need answered.</h2>
          <div className="grid gap-3 sm:grid-cols-2">{[
            ["Choosing AI tools", "Comparisons and practical buyer guides", "/articles?category=comparisons"],
            ["Building with agents", "Workflows, reliability and real-world use", "/articles?tag=agents"],
            ["Understanding models", "Clear explainers without the benchmark fog", "/articles?category=guides"],
            ["Tracking the industry", "Companies, policy, funding and power", "/articles?category=news"],
          ].map(([title, description, path]) => <Link key={title} to={path} className="topic-path"><strong>{title}</strong><span>{description}</span><b aria-hidden>→</b></Link>)}</div>
        </div>
      </section>
    </main>

    <div className="mx-auto max-w-7xl px-5 sm:px-8"><AdSlot slot="aion-footer" className="mb-8" /></div>
    <footer className="border-t border-line bg-surface/40">
      <div className="mx-auto grid max-w-7xl gap-8 px-5 py-10 sm:px-8 md:grid-cols-[1.2fr_2fr]">
        <div><Link to="/" className="brand-lockup"><span className="brand-mark" aria-hidden>A</span><span><strong>AION</strong><small>AI NEWS</small></span></Link><p className="mt-4 max-w-xs text-sm leading-relaxed text-slateui">Independent AI intelligence for builders, leaders and curious minds.</p></div>
        <div className="footer-links grid grid-cols-2 gap-6 text-sm sm:grid-cols-3">
          <div><p className="footer-title">Explore</p><Link to="/articles">Latest</Link><Link to="/categories">Categories</Link><Link to="/tags">Topics</Link></div>
          <div><p className="footer-title">Standards</p><Link to="/about">About</Link><Link to="/editorial-policy">Editorial policy</Link><Link to="/corrections-policy">Corrections</Link></div>
          <div><p className="footer-title">Legal</p><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link><Link to="/contact">Contact</Link></div>
        </div>
      </div>
      <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-2 border-t border-line px-5 py-5 text-xs text-slateui sm:px-8"><span>© {new Date().getFullYear()} AION AI News</span><span>Built by agents. Supervised by humans.</span></div>
    </footer>
  </div>;
}
