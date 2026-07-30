import { useEffect, useState } from "react";
import { Nav } from "./Landing";
import { API_BASE } from "../lib/api";
import { usePageMetadata } from "../lib/seo";

function Pagina({ tag, titulo, children }: { tag: string; titulo: string; children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Nav />
      <main id="main-content" className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-2">{tag}</p>
        <h1 className="font-display text-4xl font-bold tracking-tight">{titulo}</h1>
        <div className="mt-6 space-y-4 leading-relaxed text-slateui">{children}</div>
      </main>
    </div>
  );
}

export function Privacy() {
  usePageMetadata({ title: "Privacy Policy", description: "How AION AI NEWS OS handles account, contact and analytics data.", path: "/privacy" });
  return (
    <Pagina tag="legal" titulo="Privacy Policy">
      <p>AION collects only the data needed to operate the platform: your name and email at sign-up, and the messages sent through the contact form.</p>
      <p>Passwords are stored exclusively as cryptographic hashes (bcrypt) — not even our team can read them. Session tokens expire automatically and can be revoked.</p>
      <p>We do not sell or share personal data with third parties. Browsing data may be used in aggregated, anonymous form to improve the portal. Third-party services (analytics, advertising) may use cookies as described in their own policies.</p>
      <p>You can request deletion of your account and data at any time via the Contact page. This policy may be updated; the current version will always live on this page.</p>
    </Pagina>
  );
}

export function Terms() {
  usePageMetadata({ title: "Terms of Use", description: "Terms governing use of the AION AI NEWS OS website and editorial content.", path: "/terms" });
  return (
    <Pagina tag="legal" titulo="Terms of Use">
      <p>By using AION you agree to these terms. The portal provides informational content about artificial intelligence, produced with the support of AI agents under human supervision.</p>
      <p>Content is provided "as is", without warranties of accuracy or fitness for a particular purpose, and does not constitute professional advice.</p>
      <p>Using the platform for illegal purposes, attempting to access restricted areas without authorization, or deliberately overloading the services is prohibited.</p>
      <p>Published content may be quoted with attribution and a link to the original article. These terms may be revised periodically.</p>
    </Pagina>
  );
}

export function EditorialPolicy() {
  usePageMetadata({
    title: "Editorial Policy",
    description: "How AION selects, verifies, reviews and publishes artificial intelligence coverage.",
    path: "/editorial-policy",
  });
  return (
    <Pagina tag="standards" titulo="Editorial Policy">
      <p>AION covers consequential developments in artificial intelligence with an emphasis on evidence, context and clear attribution.</p>
      <p>Automated agents may assist research, drafting, image selection and quality checks. Publication gates verify source links, originality, language, metadata and image requirements before an article becomes public.</p>
      <p>AI assistance never removes editorial accountability. Material claims should be traceable to identified sources, uncertainty must be disclosed, and promotional claims are not presented as independent findings.</p>
    </Pagina>
  );
}

export function CorrectionsPolicy() {
  usePageMetadata({
    title: "Corrections Policy",
    description: "How readers can report errors and how AION corrects published coverage.",
    path: "/corrections-policy",
  });
  return (
    <Pagina tag="standards" titulo="Corrections Policy">
      <p>Accuracy concerns can be submitted through the Contact page with the article URL, the disputed passage and supporting evidence.</p>
      <p>Substantive errors are reviewed promptly. Confirmed errors are corrected in the article, while significant changes are recorded transparently instead of silently changing the meaning of the original coverage.</p>
      <p>Updates that add new information without correcting an error may be identified as updates. Requests to change accurate reporting are not treated as corrections.</p>
    </Pagina>
  );
}

export function Contact() {
  usePageMetadata({ title: "Contact", description: "Contact the AION AI NEWS OS newsroom with questions, story tips or partnership proposals.", path: "/contact" });
  const [v, setV] = useState({ name: "", email: "", message: "" });
  const [ok, setOk] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setOk(""); setErro(""); setEnviando(true);
    try {
      const r = await fetch(`${API_BASE}/api/public/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(v),
      });
      const b = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(b.detail || "Failed to send the message");
      setOk(b.detail); setV({ name: "", email: "", message: "" });
    } catch (err: any) { setErro(err.message); }
    finally { setEnviando(false); }
  }

  return (
    <Pagina tag="get in touch" titulo="Contact">
      <p>Questions, story tips or partnerships? Send us a message.</p>
      <form onSubmit={enviar} className="mt-2 max-w-md space-y-4 text-ink">
        <label className="block text-sm font-medium">Name
          <input className="field mt-1.5" required minLength={2} value={v.name}
            onChange={(e) => setV({ ...v, name: e.target.value })} />
        </label>
        <label className="block text-sm font-medium">Email
          <input className="field mt-1.5" type="email" required value={v.email}
            onChange={(e) => setV({ ...v, email: e.target.value })} />
        </label>
        <label className="block text-sm font-medium">Message
          <textarea className="field mt-1.5 min-h-[120px]" required minLength={5} value={v.message}
            onChange={(e) => setV({ ...v, message: e.target.value })} />
        </label>
        {ok && <p className="rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300" aria-live="polite">{ok}</p>}
        {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">{erro}</p>}
        <button className="btn-primary" disabled={enviando}>{enviando ? "Sending…" : "Send message"}</button>
      </form>
    </Pagina>
  );
}

export function Taxonomia({ tipo }: { tipo: "categories" | "tags" }) {
  const isCategories = tipo === "categories";
  usePageMetadata({
    title: isCategories ? "AI categories" : "AI topics",
    description: isCategories ? "Explore AION artificial intelligence coverage by category." : "Explore AION artificial intelligence coverage by topic and tag.",
    path: isCategories ? "/categories" : "/tags",
  });
  const [itens, setItens] = useState<any[] | null>(null);
  const [erro, setErro] = useState("");
  useEffect(() => {
    setErro(""); setItens(null);
    fetch(`${API_BASE}/api/public/${tipo === "categories" ? "categories" : "tags"}`)
      .then((r) => { if (!r.ok) throw new Error("Topics are temporarily unavailable."); return r.json(); })
      .then(setItens)
      .catch((error: Error) => { setItens([]); setErro(error.message); });
  }, [tipo]);
  const chave = tipo === "categories" ? "category" : "tag";
  return (
    <Pagina tag="explore" titulo={tipo === "categories" ? "Categories" : "Tags"}>
      {itens === null ? <p className="font-mono text-sm">loading…</p>
        : erro ? <p className="rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">{erro}</p>
        : itens.length === 0 ? (
          <p>No {tipo === "categories" ? "categories" : "tags"} yet — they will appear when published articles use them.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {itens.map((i) => (
              <a key={i[chave]} href={`/articles?${tipo === "categories" ? "category" : "tag"}=${encodeURIComponent(i[chave])}`}
                className="chip">
                {i[chave]} <span className="font-mono text-xs text-slateui">({i.total})</span>
              </a>
            ))}
          </div>
        )}
    </Pagina>
  );
}
