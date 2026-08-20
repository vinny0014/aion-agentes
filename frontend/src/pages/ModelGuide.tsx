import { Link } from "react-router-dom";
import { usePageMetadata } from "../lib/seo";
import { Nav } from "./Landing";

const MODELS = {
  chatgpt: { name: "ChatGPT", maker: "OpenAI", summary: "A general-purpose AI product spanning conversation, reasoning, files, multimodal work and tools.", best: ["Broad everyday and professional workflows", "Tool-rich tasks and rapid prototyping", "Teams that value a large product ecosystem"], watch: ["The product may route work across changing model versions", "Plan limits and feature availability can vary", "Sensitive workflows still need human review"], desk: "/openai" },
  claude: { name: "Claude", maker: "Anthropic", summary: "An AI assistant and model family focused on complex knowledge work, coding and careful instruction following.", best: ["Long documents and structured synthesis", "Coding and iterative knowledge work", "Tasks where tone and instruction discipline matter"], watch: ["Features and limits differ by plan and region", "Outputs require source verification", "Long context does not guarantee perfect recall"], desk: "/anthropic" },
  gemini: { name: "Gemini", maker: "Google", summary: "Google’s model and assistant family, designed for multimodal work and integration across Google products.", best: ["Multimodal inputs", "Workflows connected to Google products", "Research and productivity use cases"], watch: ["Capabilities differ across Gemini surfaces", "Workspace permissions need careful review", "Benchmark claims may not predict your workflow"], desk: "/google-ai" },
  llama: { name: "Llama", maker: "Meta", summary: "An open-weight model family used for customizable and self-managed AI deployments.", best: ["Teams needing deployment control", "Customization and domain adaptation", "Infrastructure-conscious builders"], watch: ["Operations, safety and monitoring shift to the deployer", "Hardware and serving costs matter", "License terms should be checked for each release"], desk: "/models" },
} as const;

export type ModelSlug = keyof typeof MODELS;
export default function ModelGuide({ model }: { model: ModelSlug }) {
  const item = MODELS[model];
  usePageMetadata({ title: `${item.name} guide — strengths, trade-offs and news`, description: item.summary, path: `/ai/${model}` });
  return <div className="min-h-screen pb-16 sm:pb-0"><Nav /><main id="main-content" className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
    <header className="border-y-2 border-ink py-9"><p className="eyebrow">AION model guide · {item.maker}</p><h1 className="mt-2 font-display text-6xl font-bold tracking-tight">{item.name}</h1><p className="mt-5 max-w-3xl text-xl leading-relaxed text-slateui">{item.summary}</p></header>
    <div className="mt-12 grid gap-10 md:grid-cols-2"><section><p className="eyebrow">Decision guide</p><h2 className="mt-2 font-display text-3xl font-bold">Often a strong fit for</h2><ul className="mt-5 space-y-4">{item.best.map(text => <li key={text} className="flex gap-3 border-t border-line pt-4"><span className="text-signal">●</span><span>{text}</span></li>)}</ul></section><section><p className="eyebrow">Trade-offs</p><h2 className="mt-2 font-display text-3xl font-bold">What to check first</h2><ul className="mt-5 space-y-4">{item.watch.map(text => <li key={text} className="flex gap-3 border-t border-line pt-4"><span className="text-signal">●</span><span>{text}</span></li>)}</ul></section></div>
    <section className="mt-14 border-y border-line py-8"><p className="eyebrow">Keep researching</p><div className="mt-3 flex flex-wrap gap-5 text-lg font-semibold"><Link to={item.desk} className="text-signal hover:underline">Latest {item.maker} coverage →</Link><Link to="/ai-arena" className="text-signal hover:underline">Compare in AI Arena →</Link><Link to="/compare/chatgpt-vs-claude" className="text-signal hover:underline">Open a head-to-head guide →</Link></div></section>
    <p className="mt-8 text-xs leading-relaxed text-slateui">Independent editorial guide. AION is not affiliated with or endorsed by {item.maker}. Capabilities, pricing and availability change; verify current product terms before making a purchase or deployment decision.</p>
  </main></div>;
}

const COMPARISONS = {
  "chatgpt-vs-claude": ["ChatGPT", "Claude", "Choose by workflow: tool breadth and product ecosystem versus long-form discipline and careful knowledge work."],
  "chatgpt-vs-gemini": ["ChatGPT", "Gemini", "Compare general-purpose tool workflows with Google-connected multimodal productivity."],
  "claude-vs-gemini": ["Claude", "Gemini", "Compare long-form knowledge work with multimodal and Google-integrated workflows."],
} as const;
export type ComparisonSlug = keyof typeof COMPARISONS;
export function ComparisonGuide({ comparison }: { comparison: ComparisonSlug }) {
  const [left, right, summary] = COMPARISONS[comparison];
  usePageMetadata({ title: `${left} vs ${right} — practical comparison`, description: summary, path: `/compare/${comparison}` });
  return <div className="min-h-screen pb-16 sm:pb-0"><Nav /><main id="main-content" className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14"><header className="border-y-2 border-ink py-9"><p className="eyebrow">AION comparison guide</p><h1 className="mt-2 font-display text-5xl font-bold tracking-tight md:text-7xl">{left} vs {right}</h1><p className="mt-5 max-w-3xl text-xl leading-relaxed text-slateui">{summary}</p></header><section className="mt-12"><h2 className="font-display text-3xl font-bold">The useful answer</h2><p className="mt-4 text-lg leading-relaxed text-slateui">There is no universal winner. Start with your highest-value recurring task, test both products with the same inputs, check source accuracy and latency, then compare privacy, controls and total operating cost. AION does not publish a winner without reproducible evidence.</p></section><div className="mt-10 flex flex-wrap gap-4"><Link to="/ai-arena" className="btn-primary">Compare another pair</Link><Link to="/models" className="btn-ghost">Read model coverage</Link></div><p className="mt-10 text-xs text-slateui">Independent editorial comparison. No paid placement or provider affiliation.</p></main></div>;
}
