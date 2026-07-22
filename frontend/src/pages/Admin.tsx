import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { AppNav } from "./Dashboard";
import { usePageMetadata } from "../lib/seo";

const ABAS = ["Users", "Agents", "Content", "Tasks", "Queue", "Logs", "Memory", "Settings"] as const;
type Aba = (typeof ABAS)[number];

function Tabela({ cols, rows, onDelete }: { cols: string[]; rows: any[]; onDelete?: (id: any) => void }) {
  if (rows.length === 0) return <p className="mt-4 text-sm text-slateui">Nothing here yet.</p>;
  return (
    <div className="mt-4 overflow-x-auto rounded-lg border border-line bg-surface">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-line">
            {cols.map((c) => <th key={c} className="px-4 py-2.5 font-mono text-[11px] uppercase tracking-wider text-slateui">{c}</th>)}
            {onDelete && <th className="px-4 py-2.5" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id ?? r.key ?? i} className="border-b border-line last:border-0">
              {cols.map((c) => (
                <td key={c} className="max-w-[280px] truncate px-4 py-2.5">{String(r[c] ?? "—")}</td>
              ))}
              {onDelete && (
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => onDelete(r.id ?? r.key)}
                    className="text-xs font-medium text-red-400 hover:underline">Delete</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Form({ campos, onSubmit, rotulo }: {
  campos: { name: string; label: string; placeholder?: string }[];
  onSubmit: (data: Record<string, string>) => Promise<void>;
  rotulo: string;
}) {
  const [v, setV] = useState<Record<string, string>>({});
  const [erro, setErro] = useState("");
  return (
    <form
      className="mt-6 flex flex-wrap items-end gap-3"
      onSubmit={async (e) => {
        e.preventDefault(); setErro("");
        try { await onSubmit(v); setV({}); } catch (err: any) { setErro(err.message); }
      }}
    >
      {campos.map((c) => (
        <label key={c.name} className="text-xs font-medium">
          {c.label}
          <input className="field mt-1 !py-2 text-sm" placeholder={c.placeholder}
            value={v[c.name] || ""} onChange={(e) => setV({ ...v, [c.name]: e.target.value })} />
        </label>
      ))}
      <button className="btn-primary !py-2 text-sm">{rotulo}</button>
      {erro && <p className="w-full text-sm text-red-400">{erro}</p>}
    </form>
  );
}

export default function Admin() {
  usePageMetadata({ title: "Administration", description: "AION administration workspace.", path: "/admin", robots: "noindex,nofollow" });
  const nav = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [aba, setAba] = useState<Aba>("Users");
  const [dados, setDados] = useState<any[]>([]);

  const rotas: Record<Aba, string> = {
    Users: "/api/users", Agents: "/api/agents", Content: "/api/contents",
    Tasks: "/api/tasks", Queue: "/api/content-queue", Logs: "/api/logs",
    Memory: "/api/memory", Settings: "/api/settings",
  };

  async function carregar(a: Aba = aba) {
    setDados(await api(rotas[a]));
  }

  useEffect(() => {
    (async () => {
      try {
        const me = await api("/api/auth/me");
        if (me.role !== "admin") { nav("/dashboard"); return; }
        setUser(me);
        await carregar();
      } catch { nav("/login"); }
    })();
  }, []);

  useEffect(() => { if (user) carregar(aba); }, [aba]);

  async function excluir(rota: string, id: any) {
    await api(`${rota}/${id}`, { method: "DELETE" });
    await carregar();
  }

  if (!user) return <div className="p-10 font-mono text-sm text-slateui">Loading…</div>;

  return (
    <div className="min-h-screen">
      <AppNav user={user} />
      <main id="main-content" className="mx-auto max-w-6xl px-6 py-10">
        <p className="tag mb-1">administration</p>
        <h1 className="font-display text-3xl font-bold">Administration dashboard</h1>

        <div className="mt-6 flex flex-wrap gap-1 border-b border-line" role="tablist">
          {ABAS.map((a) => (
            <button key={a} role="tab" aria-selected={aba === a} onClick={() => setAba(a)}
              className={`px-3.5 py-2 text-sm font-medium transition ${
                aba === a ? "border-b-2 border-ultra text-ultra" : "text-slateui hover:text-ink"}`}>
              {a}
            </button>
          ))}
        </div>

        {aba === "Users" && (
          <Tabela cols={["id", "name", "email", "role", "is_active"]} rows={dados}
            onDelete={(id) => excluir("/api/users", id)} />
        )}

        {aba === "Agents" && (<>
          <Form rotulo="Create agent" campos={[
            { name: "slug", label: "Slug", placeholder: "my-agent" },
            { name: "name", label: "Name" }, { name: "role", label: "Role" },
          ]} onSubmit={async (v) => {
            await api("/api/agents", { method: "POST", body: JSON.stringify(v) });
            await carregar();
          }} />
          <Tabela cols={["id", "slug", "name", "role", "classification", "status"]} rows={dados}
            onDelete={(id) => excluir("/api/agents", id)} />
        </>)}

        {aba === "Content" && (<>
          <Link to="/admin/editor/new" className="btn-primary mt-6 !py-2 text-sm">New article</Link>
          {dados.length === 0 ? <p className="mt-4 text-sm text-slateui">No content yet.</p> : (
            <div className="mt-4 overflow-x-auto rounded-lg border border-line bg-surface">
              <table className="w-full text-left text-sm">
                <thead><tr className="border-b border-line">
                  {["id","title","slug","status","published_at"].map((c) =>
                    <th key={c} className="px-4 py-2.5 font-mono text-[11px] uppercase tracking-wider text-slateui">{c}</th>)}
                  <th className="px-4 py-2.5" />
                </tr></thead>
                <tbody>{dados.map((r: any) => (
                  <tr key={r.id} className="border-b border-line last:border-0">
                    <td className="px-4 py-2.5">{r.id}</td>
                    <td className="max-w-[280px] truncate px-4 py-2.5">{r.title}</td>
                    <td className="max-w-[200px] truncate px-4 py-2.5 font-mono text-xs">{r.slug}</td>
                    <td className="px-4 py-2.5">{r.status}</td>
                    <td className="px-4 py-2.5">{r.published_at ?? "—"}</td>
                    <td className="px-4 py-2.5 text-right whitespace-nowrap">
                      <Link to={`/admin/editor/${r.id}`} className="mr-3 text-xs font-medium text-ultra hover:underline">Edit</Link>
                      <button onClick={() => excluir("/api/contents", r.id)}
                        className="text-xs font-medium text-red-400 hover:underline">Delete</button>
                    </td>
                  </tr>))}
                </tbody>
              </table>
            </div>
          )}
        </>)}

        {aba === "Tasks" && (<>
          <Form rotulo="Create task" campos={[
            { name: "title", label: "Title" }, { name: "description", label: "Description" },
          ]} onSubmit={async (v) => {
            await api("/api/tasks", { method: "POST", body: JSON.stringify(v) });
            await carregar();
          }} />
          <Tabela cols={["id", "title", "status", "priority", "due_at"]} rows={dados}
            onDelete={(id) => excluir("/api/tasks", id)} />
        </>)}

        {aba === "Queue" && (<>
          <Form rotulo="Add to queue" campos={[
            { name: "topic", label: "Article topic", placeholder: "AI trends in 2026" },
          ]} onSubmit={async (v) => {
            await api("/api/content-queue", { method: "POST", body: JSON.stringify(v) });
            await carregar();
          }} />
          <button className="btn-ghost mt-3 !py-2 text-sm"
            onClick={async () => { await api("/api/pipeline/run", { method: "POST" }); await carregar(); }}>
            Process queue now
          </button>
          <Tabela cols={["id", "topic", "provider", "status", "error"]} rows={dados}
            onDelete={(id) => excluir("/api/content-queue", id)} />
        </>)}

        {aba === "Logs" && (
          <Tabela cols={["id", "level", "source", "message", "created_at"]} rows={dados} />
        )}

        {aba === "Memory" && (<>
          <Form rotulo="Save memory" campos={[
            { name: "scope", label: "Scope", placeholder: "global" },
            { name: "key", label: "Key" }, { name: "value", label: "Value" },
          ]} onSubmit={async (v) => {
            await api("/api/memory", { method: "PUT", body: JSON.stringify({ scope: v.scope || "global", ...v }) });
            await carregar();
          }} />
          <Tabela cols={["id", "scope", "key", "value", "updated_at"]} rows={dados}
            onDelete={(id) => excluir("/api/memory", id)} />
        </>)}

        {aba === "Settings" && (<>
          <p className="mt-4 rounded-md bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            Secrets and API keys are not accepted here — set them in the backend .env file.
          </p>
          <Form rotulo="Save" campos={[
            { name: "key", label: "Key", placeholder: "posts_per_day" },
            { name: "value", label: "Value", placeholder: "3" },
          ]} onSubmit={async (v) => {
            await api("/api/settings", { method: "PUT", body: JSON.stringify(v) });
            await carregar();
          }} />
          <Tabela cols={["key", "value", "updated_at"]} rows={dados}
            onDelete={(key) => excluir("/api/settings", key)} />
        </>)}
      </main>
    </div>
  );
}
