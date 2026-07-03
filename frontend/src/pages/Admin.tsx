import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { AppNav } from "./Dashboard";

const ABAS = ["Usuários", "Agentes", "Conteúdo", "Tarefas", "Fila", "Logs", "Memória", "Configurações"] as const;
type Aba = (typeof ABAS)[number];

function Tabela({ cols, rows, onDelete }: { cols: string[]; rows: any[]; onDelete?: (id: any) => void }) {
  if (rows.length === 0) return <p className="mt-4 text-sm text-slateui">Nada por aqui ainda.</p>;
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
                    className="text-xs font-medium text-red-400 hover:underline">Excluir</button>
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
  const nav = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [aba, setAba] = useState<Aba>("Usuários");
  const [dados, setDados] = useState<any[]>([]);

  const rotas: Record<Aba, string> = {
    Usuários: "/api/users", Agentes: "/api/agents", Conteúdo: "/api/contents",
    Tarefas: "/api/tasks", Fila: "/api/content-queue", Logs: "/api/logs",
    Memória: "/api/memory", Configurações: "/api/settings",
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

  if (!user) return <div className="p-10 font-mono text-sm text-slateui">carregando…</div>;

  return (
    <div className="min-h-screen">
      <AppNav user={user} />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="tag mb-1">administração</p>
        <h1 className="font-display text-3xl font-bold">Painel administrativo</h1>

        <div className="mt-6 flex flex-wrap gap-1 border-b border-line" role="tablist">
          {ABAS.map((a) => (
            <button key={a} role="tab" aria-selected={aba === a} onClick={() => setAba(a)}
              className={`px-3.5 py-2 text-sm font-medium transition ${
                aba === a ? "border-b-2 border-ultra text-ultra" : "text-slateui hover:text-ink"}`}>
              {a}
            </button>
          ))}
        </div>

        {aba === "Usuários" && (
          <Tabela cols={["id", "name", "email", "role", "is_active"]} rows={dados}
            onDelete={(id) => excluir("/api/users", id)} />
        )}

        {aba === "Agentes" && (<>
          <Form rotulo="Criar agente" campos={[
            { name: "slug", label: "Slug", placeholder: "meu-agente" },
            { name: "name", label: "Nome" }, { name: "role", label: "Função" },
          ]} onSubmit={async (v) => {
            await api("/api/agents", { method: "POST", body: JSON.stringify(v) });
            await carregar();
          }} />
          <Tabela cols={["id", "slug", "name", "role", "status"]} rows={dados}
            onDelete={(id) => excluir("/api/agents", id)} />
        </>)}

        {aba === "Conteúdo" && (<>
          <Link to="/admin/editor/novo" className="btn-primary mt-6 !py-2 text-sm">Novo artigo</Link>
          {dados.length === 0 ? <p className="mt-4 text-sm text-slateui">Nenhum conteúdo ainda.</p> : (
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
                      <Link to={`/admin/editor/${r.id}`} className="mr-3 text-xs font-medium text-ultra hover:underline">Editar</Link>
                      <button onClick={() => excluir("/api/contents", r.id)}
                        className="text-xs font-medium text-red-400 hover:underline">Excluir</button>
                    </td>
                  </tr>))}
                </tbody>
              </table>
            </div>
          )}
        </>)}

        {aba === "Tarefas" && (<>
          <Form rotulo="Criar tarefa" campos={[
            { name: "title", label: "Título" }, { name: "description", label: "Descrição" },
          ]} onSubmit={async (v) => {
            await api("/api/tasks", { method: "POST", body: JSON.stringify(v) });
            await carregar();
          }} />
          <Tabela cols={["id", "title", "status", "priority", "due_at"]} rows={dados}
            onDelete={(id) => excluir("/api/tasks", id)} />
        </>)}

        {aba === "Fila" && (<>
          <Form rotulo="Adicionar à fila" campos={[
            { name: "topic", label: "Tópico do artigo", placeholder: "Tendências de IA em 2026" },
          ]} onSubmit={async (v) => {
            await api("/api/content-queue", { method: "POST", body: JSON.stringify(v) });
            await carregar();
          }} />
          <button className="btn-ghost mt-3 !py-2 text-sm"
            onClick={async () => { await api("/api/pipeline/run", { method: "POST" }); await carregar(); }}>
            Processar fila agora
          </button>
          <Tabela cols={["id", "topic", "provider", "status", "error"]} rows={dados}
            onDelete={(id) => excluir("/api/content-queue", id)} />
        </>)}

        {aba === "Logs" && (
          <Tabela cols={["id", "level", "source", "message", "created_at"]} rows={dados} />
        )}

        {aba === "Memória" && (<>
          <Form rotulo="Salvar memória" campos={[
            { name: "scope", label: "Escopo", placeholder: "global" },
            { name: "key", label: "Chave" }, { name: "value", label: "Valor" },
          ]} onSubmit={async (v) => {
            await api("/api/memory", { method: "PUT", body: JSON.stringify({ scope: v.scope || "global", ...v }) });
            await carregar();
          }} />
          <Tabela cols={["id", "scope", "key", "value", "updated_at"]} rows={dados}
            onDelete={(id) => excluir("/api/memory", id)} />
        </>)}

        {aba === "Configurações" && (<>
          <p className="mt-4 rounded-md bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            Segredos e chaves de API não são aceitos aqui — configure-os no arquivo .env do backend.
          </p>
          <Form rotulo="Salvar" campos={[
            { name: "key", label: "Chave", placeholder: "posts_por_dia" },
            { name: "value", label: "Valor", placeholder: "3" },
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
