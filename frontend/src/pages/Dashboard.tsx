import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, clearTokens } from "../lib/api";

type User = { id: number; name: string; email: string; role: string };

export function AppNav({ user }: { user: User | null }) {
  const nav = useNavigate();
  function sair() { clearTokens(); nav("/"); }
  return (
    <nav className="glass-nav">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/dashboard" className="font-display text-lg font-bold">
          AION<span className="text-ultra">·</span>AGENTES
        </Link>
        <div className="flex items-center gap-3 text-sm">
          {user?.role === "admin" && (
            <Link to="/admin" className="px-2 py-1 text-slateui hover:text-ink">Administração</Link>
          )}
          <span className="hidden font-mono text-xs text-slateui sm:inline">{user?.email}</span>
          <button onClick={sair} className="btn-ghost !px-3 !py-1.5 text-sm">Sign out</button>
        </div>
      </div>
    </nav>
  );
}

export default function Dashboard() {
  const nav = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [contents, setContents] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const me = await api("/api/auth/me");
        setUser(me);
        const [h, a, t, c] = await Promise.all([
          api("/api/health"), api("/api/agents"), api("/api/tasks"), api("/api/contents"),
        ]);
        setHealth(h); setAgents(a); setTasks(t); setContents(c);
      } catch {
        nav("/login");
      }
    })();
  }, []);

  if (!user) return <div className="p-10 font-mono text-sm text-slateui">loading…</div>;

  const abertas = tasks.filter((t) => t.status !== "done").length;
  const publisheds = contents.filter((c) => c.status === "published").length;

  return (
    <div className="min-h-screen">
      <AppNav user={user} />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="tag mb-1">painel</p>
        <h1 className="font-display text-3xl font-bold">Olá, {user.name.split(" ")[0]}</h1>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <p className="tag">sistema</p>
            <p className="mt-2 font-mono text-sm">
              <span className={`status-dot mr-1.5 inline-block h-2 w-2 rounded-full align-middle ${health?.status === "ok" ? "bg-signal" : "bg-red-500"}`} />
              {health?.status === "ok" ? "operacional" : "degradado"}
            </p>
          </div>
          <div className="card">
            <p className="tag">agentes</p>
            <p className="mt-1 font-display text-2xl font-bold">{agents.length}</p>
          </div>
          <div className="card">
            <p className="tag">tarefas abertas</p>
            <p className="mt-1 font-display text-2xl font-bold">{abertas}</p>
          </div>
          <div className="card">
            <p className="tag">conteúdos publisheds</p>
            <p className="mt-1 font-display text-2xl font-bold">{publisheds}</p>
          </div>
        </div>

        <section className="mt-10">
          <h2 className="font-display text-xl font-bold">Equipe de agentes</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((a) => (
              <div key={a.id} className="card card-hover !p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{a.name}</span>
                  <span className="tag">{a.status}</span>
                </div>
                <p className="mt-1.5 text-xs text-slateui">{a.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-10">
          <h2 className="font-display text-xl font-bold">Últimos conteúdos</h2>
          {contents.length === 0 ? (
            <p className="mt-3 text-sm text-slateui">
              No content yet. Create the first one in Admin or add a topic to the publishing queue.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {contents.slice(0, 8).map((c) => (
                <li key={c.id} className="card flex items-center justify-between !py-3">
                  <span className="text-sm font-medium">{c.title}</span>
                  <span className="tag">{c.status}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
