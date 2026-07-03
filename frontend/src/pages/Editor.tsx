import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { AppNav } from "./Dashboard";

function slugify(t: string) {
  return t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 200);
}

export default function Editor() {
  const nav = useNavigate();
  const { id } = useParams(); // "novo" ou id numérico
  const novo = id === "novo";
  const [user, setUser] = useState<any>(null);
  const [v, setV] = useState({
    title: "", slug: "", excerpt: "", body: "", seo_title: "", seo_description: "", status: "draft", category: "", tags: "",
  });
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const me = await api("/api/auth/me");
        setUser(me);
        if (!novo) {
          const c = await api(`/api/contents/${id}`);
          setV({
            title: c.title, slug: c.slug, excerpt: c.excerpt, body: c.body,
            seo_title: c.seo_title, seo_description: c.seo_description, status: c.status,
            category: c.category || "", tags: c.tags || "",
          });
        }
      } catch { nav("/login"); }
    })();
  }, [id]);

  function set(campo: string, valor: string) {
    setV((old) => {
      const next = { ...old, [campo]: valor };
      if (campo === "title" && novo) next.slug = slugify(valor);
      return next;
    });
  }

  async function salvar(status?: string) {
    setErro(""); setMsg(""); setSalvando(true);
    const payload = { ...v, ...(status ? { status } : {}) };
    try {
      if (novo) {
        const criado = await api("/api/contents", { method: "POST", body: JSON.stringify(payload) });
        setMsg(status === "published" ? "Artigo publicado" : "Rascunho salvo");
        nav(`/admin/editor/${criado.id}`, { replace: true });
      } else {
        const { slug, ...rest } = payload; // slug é imutável após criação
        await api(`/api/contents/${id}`, { method: "PATCH", body: JSON.stringify(rest) });
        if (status) setV((old) => ({ ...old, status }));
        setMsg(status === "published" ? "Artigo publicado" : status === "draft" ? "Despublicado (rascunho)" : "Alterações salvas");
      }
    } catch (e: any) { setErro(e.message); }
    finally { setSalvando(false); }
  }

  if (!user) return <div className="p-10 font-mono text-sm text-slateui">carregando…</div>;

  return (
    <div className="min-h-screen">
      <AppNav user={user} />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="tag mb-1">editor · {v.status === "published" ? "publicado" : v.status === "queued" ? "na fila" : "rascunho"}</p>
            <h1 className="font-display text-3xl font-bold">{novo ? "Novo artigo" : "Editar artigo"}</h1>
          </div>
          <div className="flex gap-2">
            <button className="btn-ghost !py-2 text-sm" disabled={salvando} onClick={() => salvar()}>
              Salvar
            </button>
            {v.status !== "published" ? (
              <button className="btn-primary !py-2 text-sm" disabled={salvando} onClick={() => salvar("published")}>
                Publicar
              </button>
            ) : (
              <button className="btn-ghost !py-2 text-sm" disabled={salvando} onClick={() => salvar("draft")}>
                Despublicar
              </button>
            )}
          </div>
        </div>

        {msg && <p className="mt-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{msg}</p>}
        {erro && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>}

        <div className="mt-8 space-y-5">
          <label className="block text-sm font-medium">
            Título
            <input className="field mt-1.5" value={v.title} onChange={(e) => set("title", e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Slug {novo ? "(gerado do título, editável)" : "(fixo após criação)"}
            <input className="field mt-1.5 font-mono text-xs" value={v.slug} disabled={!novo}
              onChange={(e) => set("slug", slugify(e.target.value))} />
          </label>
          <label className="block text-sm font-medium">
            Resumo
            <input className="field mt-1.5" value={v.excerpt} onChange={(e) => set("excerpt", e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Corpo <span className="font-normal text-slateui">(parágrafos separados por linha em branco; "## " cria subtítulo)</span>
            <textarea className="field mt-1.5 min-h-[320px] font-mono text-sm" value={v.body}
              onChange={(e) => set("body", e.target.value)} />
          </label>
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block text-sm font-medium">
              Categoria <span className="font-normal text-slateui">(uma, ex.: noticias)</span>
              <input className="field mt-1.5" value={v.category} onChange={(e) => set("category", e.target.value)} />
            </label>
            <label className="block text-sm font-medium">
              Tags <span className="font-normal text-slateui">(separadas por vírgula)</span>
              <input className="field mt-1.5" value={v.tags} onChange={(e) => set("tags", e.target.value)} />
            </label>
          </div>
          <fieldset className="card">
            <legend className="tag px-1">seo</legend>
            <label className="block text-sm font-medium">
              Título SEO
              <input className="field mt-1.5" value={v.seo_title} placeholder={v.title}
                onChange={(e) => set("seo_title", e.target.value)} />
            </label>
            <label className="mt-4 block text-sm font-medium">
              Meta description
              <input className="field mt-1.5" value={v.seo_description} placeholder={v.excerpt}
                maxLength={160} onChange={(e) => set("seo_description", e.target.value)} />
              <span className="mt-1 block text-xs font-normal text-slateui">{v.seo_description.length}/160</span>
            </label>
          </fieldset>
        </div>
      </main>
    </div>
  );
}
