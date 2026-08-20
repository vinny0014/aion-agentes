import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { usePageMetadata } from "../lib/seo";
import { trackEvent } from "../lib/telemetry";
import { Nav } from "./Landing";

const MODELS = [
  { name: "ChatGPT", maker: "OpenAI", strengths: "General reasoning, tools and a broad product ecosystem", watch: "Model and product versions change quickly", href: "/ai/chatgpt" },
  { name: "Claude", maker: "Anthropic", strengths: "Long-form work, coding and careful instruction following", watch: "Availability varies by product and region", href: "/ai/claude" },
  { name: "Gemini", maker: "Google", strengths: "Multimodal workflows and Google product integration", watch: "Capabilities differ across tiers and surfaces", href: "/ai/gemini" },
  { name: "Llama", maker: "Meta", strengths: "Open-weight deployment and customization", watch: "Teams own more of the safety and operations stack", href: "/ai/llama" },
] as const;

export default function Arena() {
  usePageMetadata({ title: "AION AI Arena — model comparisons", description: "A transparent, editorially maintained guide to comparing leading AI model families by real use case.", path: "/ai-arena" });
  const [left, setLeft] = useState(0); const [right, setRight] = useState(1); const [choice, setChoice] = useState<string | null>(null);
  const pair = useMemo(() => [MODELS[left], MODELS[right]], [left, right]);
  const choose = (name: string) => { setChoice(name); localStorage.setItem(`aion-arena:${pair.map(m => m.name).sort().join(":")}`, name); trackEvent("arena_vote", { choice: name, comparison: pair.map(m => m.name).join("_vs_") }); };
  return <div className="min-h-screen pb-16 sm:pb-0"><Nav /><main id="main-content" className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14">
    <header className="grid gap-8 border-y-2 border-ink py-10 lg:grid-cols-[1.35fr_.65fr] lg:items-end"><div><p className="eyebrow">AION AI Arena · beta</p><h1 className="mt-2 font-display text-5xl font-bold leading-none tracking-tight md:text-7xl">Compare models without the leaderboard theater.</h1></div><div><p className="text-lg leading-relaxed text-slateui">A transparent decision guide built around use cases, trade-offs and evidence. No paid placement. No invented community totals.</p><Link to="/editorial-policy" className="mt-4 inline-block text-sm font-semibold text-signal hover:underline">How AION evaluates claims →</Link></div></header>
    <section className="mt-14" aria-labelledby="head-to-head"><div className="section-heading"><div><p className="eyebrow">Head to head</p><h2 id="head-to-head">Which model would you choose?</h2></div><p className="max-w-md text-sm text-slateui">This beta saves only your choice on this device. A public ranking will appear only after auditable server-side aggregation is ready.</p></div>
      <div className="mb-6 grid gap-3 sm:grid-cols-2"><select className="field" value={left} onChange={e => { setLeft(Number(e.target.value)); setChoice(null); }}>{MODELS.map((m,i) => <option key={m.name} value={i} disabled={i===right}>{m.name}</option>)}</select><select className="field" value={right} onChange={e => { setRight(Number(e.target.value)); setChoice(null); }}>{MODELS.map((m,i) => <option key={m.name} value={i} disabled={i===left}>{m.name}</option>)}</select></div>
      <div className="grid gap-5 md:grid-cols-2">{pair.map(model => <article key={model.name} className="border border-line bg-surface/40 p-7"><p className="eyebrow">{model.maker}</p><h3 className="mt-2 font-display text-4xl font-bold">{model.name}</h3><dl className="mt-6 space-y-4 text-sm"><div><dt className="font-bold text-ink">Often strong for</dt><dd className="mt-1 text-slateui">{model.strengths}</dd></div><div><dt className="font-bold text-ink">Watch closely</dt><dd className="mt-1 text-slateui">{model.watch}</dd></div></dl><button onClick={() => choose(model.name)} className="btn-primary mt-7 w-full">Choose {model.name}</button>{choice === model.name && <p className="mt-3 text-center text-sm font-semibold text-signal" aria-live="polite">Saved on this device</p>}</article>)}</div>
    </section>
    <p className="mt-8 border-l-2 border-line pl-4 text-xs leading-relaxed text-slateui">AION AI Arena is an independent editorial product. AION is not affiliated with, endorsed by or sponsored by the model providers listed here. Product names are used for identification and comparison.</p>
    <section className="mt-16"><div className="section-heading"><div><p className="eyebrow">Model directory</p><h2>Start with the trade-off</h2></div></div><div className="grid border-l border-t border-line sm:grid-cols-2 lg:grid-cols-4">{MODELS.map(model => <Link key={model.name} to={model.href} className="group border-b border-r border-line p-5"><p className="eyebrow">{model.maker}</p><h3 className="mt-2 font-display text-2xl font-bold group-hover:text-signal">{model.name} →</h3><p className="mt-3 text-sm text-slateui">{model.strengths}</p></Link>)}</div></section>
  </main></div>;
}
