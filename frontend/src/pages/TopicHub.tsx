import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import EditorialImage from "../components/EditorialImage";
import { API_BASE } from "../lib/api";
import { usePageMetadata } from "../lib/seo";
import { trackEvent } from "../lib/telemetry";
import { Nav } from "./Landing";

type Story = { id: number; title: string; slug: string; excerpt?: string; category?: string; published_at: string; reading_time?: number; image_url?: string; image_alt?: string; };

export const TOPIC_HUBS = {
  openai: { title: "OpenAI", description: "Reporting and analysis on OpenAI products, research, leadership and strategy.", filter: "tag=openai" },
  anthropic: { title: "Anthropic", description: "Claude, safety research, enterprise adoption and the company building them.", filter: "tag=anthropic" },
  "google-ai": { title: "Google & DeepMind", description: "Gemini, DeepMind research and Google’s AI product strategy.", filter: "tag=google" },
  models: { title: "Models", description: "Frontier model releases, evaluations, capabilities and limitations in context.", filter: "tag=models" },
  "ai-agents": { title: "AI Agents", description: "Agentic workflows, tools, reliability and real-world deployments.", filter: "tag=agents" },
  "ai-infrastructure": { title: "AI Infrastructure", description: "Chips, cloud, energy, data centers and the systems beneath AI.", filter: "tag=infrastructure" },
  robotics: { title: "Robotics", description: "Embodied intelligence, automation and the machines moving AI into the physical world.", filter: "tag=robotics" },
  business: { title: "AI Business", description: "Funding, deals, enterprise adoption and the economics of artificial intelligence.", filter: "category=news" },
  policy: { title: "AI Policy", description: "Regulation, courts, standards, safety and the public interest.", filter: "tag=policy" },
  research: { title: "AI Research", description: "Important papers and scientific progress, explained beyond the abstract.", filter: "category=research" },
  analysis: { title: "Analysis", description: "Source-led interpretation of what consequential AI developments mean.", filter: "category=analysis" },
  guides: { title: "Guides", description: "Practical, decision-useful AI explainers without the hype.", filter: "category=guides" },
} as const;

export default function TopicHub({ hub }: { hub: keyof typeof TOPIC_HUBS }) {
  const desk = TOPIC_HUBS[hub];
  const path = `/${hub}`;
  const [stories, setStories] = useState<Story[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const perPage = 12;
  usePageMetadata({ title: `${desk.title} news and analysis`, description: desk.description, path, robots: total !== null && total >= 3 ? "index,follow,max-image-preview:large" : "noindex,follow" });

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/public/articles?${desk.filter}&page=${page}&per_page=${perPage}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("desk unavailable")))
      .then((data) => { setStories(data.items || []); setTotal(Number(data.total || 0)); })
      .catch(() => { setStories([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, [desk.filter, page]);

  const pages = Math.max(1, Math.ceil((total || 0) / perPage));
  return <div className="min-h-screen pb-16 sm:pb-0"><Nav /><main id="main-content" className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14">
    <header className="grid gap-8 border-y-2 border-ink py-8 md:grid-cols-[1.25fr_.75fr] md:items-end">
      <div><p className="eyebrow">AION coverage desk</p><h1 className="mt-2 font-display text-5xl font-bold tracking-tight md:text-7xl">{desk.title}</h1></div>
      <p className="text-lg leading-relaxed text-slateui">{desk.description}</p>
    </header>
    {loading ? <div className="mt-10 grid gap-7 md:grid-cols-3">{[1,2,3].map(i => <div key={i} className="skeleton aspect-[4/3]" />)}</div> : stories.length ? <>
      <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <article><Link to={`/article/${stories[0].slug}`} onClick={() => trackEvent("topic_click", { topic: hub, placement: "hub_lead" })} className="editorial-image block aspect-[16/9]"><EditorialImage src={stories[0].image_url} alt={stories[0].image_alt || stories[0].title} category={stories[0].category} priority className="h-full w-full object-cover" /></Link><p className="eyebrow mt-5">Lead story</p><Link to={`/article/${stories[0].slug}`}><h2 className="mt-2 font-display text-4xl font-bold leading-tight hover:text-signal">{stories[0].title}</h2></Link>{stories[0].excerpt && <p className="mt-3 text-slateui">{stories[0].excerpt}</p>}</article>
        <div className="divide-y divide-line border-t border-line">{stories.slice(1,5).map(story => <article key={story.id} className="py-5"><p className="eyebrow">{story.category || desk.title}</p><Link to={`/article/${story.slug}`}><h2 className="mt-1 font-display text-2xl font-bold leading-tight hover:text-signal">{story.title}</h2></Link><p className="story-meta">{new Date(story.published_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</p></article>)}</div>
      </div>
      <section className="mt-16"><div className="section-heading"><div><p className="eyebrow">The full desk</p><h2>More {desk.title}</h2></div><span className="text-sm text-slateui">{total} stories</span></div><div className="grid gap-x-8 border-t border-line md:grid-cols-2">{stories.slice(5).map(story => <article key={story.id} className="border-b border-line py-6"><p className="eyebrow">{story.category || desk.title}</p><Link to={`/article/${story.slug}`}><h3 className="mt-1 font-display text-2xl font-bold leading-tight hover:text-signal">{story.title}</h3></Link>{story.excerpt && <p className="mt-2 line-clamp-2 text-sm text-slateui">{story.excerpt}</p>}</article>)}</div></section>
      {pages > 1 && <nav aria-label="Desk pagination" className="mt-8 flex items-center gap-4"><button className="btn-ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button><span className="text-sm text-slateui">{page} / {pages}</span><button className="btn-ghost" disabled={page === pages} onClick={() => setPage(p => p + 1)}>Next</button></nav>}
    </> : <div className="empty-state mt-10"><h2 className="font-display text-2xl font-bold text-ink">This desk is being assembled.</h2><p>We will index this page when it has enough original reporting to be useful.</p><Link className="text-signal hover:underline" to="/articles">Read the latest stories →</Link></div>}
  </main></div>;
}
