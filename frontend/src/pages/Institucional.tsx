import { useEffect, useState } from "react";
import { Nav } from "./Landing";

const BASE = import.meta.env.VITE_API_URL || "";

function Pagina({ tag, titulo, children }: { tag: string; titulo: string; children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-2">{tag}</p>
        <h1 className="font-display text-4xl font-bold tracking-tight">{titulo}</h1>
        <div className="mt-6 space-y-4 leading-relaxed text-slateui">{children}</div>
      </main>
    </div>
  );
}

export function Privacy() {
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
  return (
    <Pagina tag="legal" titulo="Terms de Uso">
      <p>By using AION you agree to these terms. The portal provides informational content about artificial intelligence, produced with the support of AI agents under human supervision.</p>
      <p>Content is provided "as is", without warranties of accuracy or fitness for a particular purpose, and does not constitute professional advice.</p>
      <p>Using the platform for illegal purposes, attempting to access restricted areas without authorization, or deliberately overloading the services is prohibited.</p>
      <p>Published content may be quoted with attribution and a link to the original article. These terms may be revised periodically.</p>
    </Pagina>
  );
}

export function Contact() {
  const [v, setV] = useState({ name: "", email: "", message: "" });
  const [ok, setOk] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setOk(""); setErro(""); setEnviando(true);
    try {
      const r = await fetch(`${BASE}/api/public/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(v),
      });
      const b = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(b.detail || "Falha ao enviar");
      setOk(b.detail); setV({ name: "", email: "", message: "" });
    } catch (err: any) { setErro(err.message); }
    finally { setEnviando(false); }
  }

  return (
    <Pagina tag="fale conosco" titulo="Contact">
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
        {ok && <p className="rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{ok}</p>}
        {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300">{erro}</p>}
        <button className="btn-primary" disabled={enviando}>{enviando ? "Enviando…" : "Send mensagem"}</button>
      </form>
    </Pagina>
  );
}

export function Taxonomia({ tipo }: { tipo: "categorias" | "tags" }) {
  const [itens, setItens] = useState<any[] | null>(null);
  useEffect(() => {
    fetch(`${BASE}/api/public/${tipo === "categorias" ? "categories" : "tags"}`)
      .then((r) => r.json()).then(setItens);
  }, [tipo]);
  const chave = tipo === "categorias" ? "category" : "tag";
  return (
    <Pagina tag="explorar" titulo={tipo === "categorias" ? "Categorias" : "Tags"}>
      {itens === null ? <p className="font-mono text-sm">loading…</p>
        : itens.length === 0 ? (
          <p>Nenhuma {tipo === "categorias" ? "categoria" : "tag"} ainda — elas aparecem aqui quando artigos publisheds as utilizam.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {itens.map((i) => (
              <a key={i[chave]} href={`/articles?${tipo === "categorias" ? "categoria" : "tag"}=${encodeURIComponent(i[chave])}`}
                className="chip">
                {i[chave]} <span className="font-mono text-xs text-slateui">({i.total})</span>
              </a>
            ))}
          </div>
        )}
    </Pagina>
  );
}
