import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, uploadEditorialImage } from "../lib/api";
import { AppNav } from "./Dashboard";
import { usePageMetadata } from "../lib/seo";

function slugify(t: string) {
  return t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 200);
}

const AUTHORS = ["AION Editorial", "Vinicio Alves", "Guest Author"];
const CATEGORIES = ["news", "guides", "comparisons", "fundamentals", "radar", "analysis"];

export default function Editor() {
  usePageMetadata({ title: "Editorial Studio", description: "AION Editorial Studio.", path: "/admin", robots: "noindex,nofollow" });
  const nav = useNavigate();
  const { id } = useParams(); // "new" or numeric id
  const novo = id === "new";
  const [user, setUser] = useState<any>(null);
  const [v, setV] = useState({
    title: "", slug: "", excerpt: "", body: "", seo_title: "", seo_description: "",
    status: "draft", category: "news", tags: "", author: "AION Editorial",
    image_url: "", image_alt: "", featured: 0, pinned: 0, breaking_flag: 0,
    editors_pick: 0, scheduled_at: "", source_url: "",
  });
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [preview, setPreview] = useState(false);

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
            category: c.category || "news", tags: c.tags || "",
            author: c.author || "AION Editorial",
            image_url: c.image_url || "", image_alt: c.image_alt || "",
            featured: +c.featured || 0, pinned: +c.pinned || 0,
            breaking_flag: +c.breaking_flag || 0, editors_pick: +c.editors_pick || 0,
            scheduled_at: c.scheduled_at || "", source_url: c.source_url || "",
          });
        }
      } catch { nav("/login"); }
    })();
  }, [id]);

  function set(campo: string, valor: any) {
    setV((old) => {
      const next = { ...old, [campo]: valor };
      if (campo === "title" && novo) next.slug = slugify(valor);
      return next;
    });
  }

  async function generateCover() {
    setErro("");
    try {
      const r = await api(`/api/orchestrator/cover?title=${encodeURIComponent(v.title || "AION")}&category=${encodeURIComponent(v.category)}`, { method: "POST" });
      set("image_url", r.image_url); set("image_alt", r.image_alt);
      setMsg("Real editorial cover generated and verified (1200×630)");
    } catch (e: any) { setErro(e.message); }
  }

  async function uploadImage(file: File) {
    setErro(""); setMsg("");
    try {
      const uploaded = await uploadEditorialImage(file, v.title || "AION");
      set("image_url", uploaded.image_url);
      set("image_alt", uploaded.image_alt);
      setMsg("Image uploaded, optimized and verified (1200×630)");
    } catch (e: any) { setErro(e.message); }
  }

  async function salvar(status?: string) {
    setErro(""); setMsg(""); setSalvando(true);
    const payload = { ...v, ...(status ? { status } : {}) };
    try {
      if (novo) {
        const criado = await api("/api/contents", { method: "POST", body: JSON.stringify(payload) });
        setMsg(status === "published" ? "Article published" : "Draft saved");
        nav(`/admin/editor/${criado.id}`, { replace: true });
      } else {
        const { slug, ...rest } = payload; // slug is immutable after creation
        await api(`/api/contents/${id}`, { method: "PATCH", body: JSON.stringify(rest) });
        if (status) setV((old) => ({ ...old, status }));
        setMsg(status === "published" ? "Article published" : status === "draft" ? "Unpublished (draft)" : "Changes saved");
      }
    } catch (e: any) { setErro(e.message); }
    finally { setSalvando(false); }
  }

  if (!user) return <div className="p-10 font-mono text-sm text-slateui">Loading…</div>;

  const paras = v.body.split(/\n\s*\n/).filter(Boolean);

  return (
    <div className="min-h-screen">
      <AppNav user={user} />
      <main id="main-content" className="mx-auto max-w-4xl px-6 py-10">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="tag mb-1">editorial studio · {v.status === "published" ? "published" : v.status === "queued" ? "queued" : "draft"}</p>
            <h1 className="font-display text-3xl font-bold">{novo ? "New article" : "Edit article"}</h1>
          </div>
          <div className="flex gap-2">
            <button className="btn-ghost !py-2 text-sm" onClick={() => setPreview(!preview)}>
              {preview ? "Back to editing" : "Preview"}
            </button>
            <button className="btn-ghost !py-2 text-sm" disabled={salvando} onClick={() => salvar()}>
              Save
            </button>
            {v.status !== "published" ? (
              <button className="btn-primary !py-2 text-sm" disabled={salvando} onClick={() => salvar("published")}>
                Publish
              </button>
            ) : (
              <button className="btn-ghost !py-2 text-sm" disabled={salvando} onClick={() => salvar("draft")}>
                Unpublish
              </button>
            )}
          </div>
        </div>

        {msg && <p className="mt-4 rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300" aria-live="polite">{msg}</p>}
        {erro && <p className="mt-4 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">{erro}</p>}

        {preview ? (
          <article className="mt-8">
            <p className="tag">{v.category} · by {v.author}</p>
            <h1 className="mt-2 font-display text-4xl font-bold leading-tight">{v.title || "(untitled)"}</h1>
            <p className="mt-3 text-slateui">{v.excerpt}</p>
            {v.image_url && <img src={v.image_url} alt={v.image_alt} className="mt-6 w-full rounded-xl border border-line object-cover" />}
            <div className="prose-body mt-8 space-y-4">
              {paras.map((p, i) => p.startsWith("## ")
                ? <h2 key={i} className="mt-8 font-display text-2xl font-bold">{p.slice(3)}</h2>
                : <p key={i}>{p}</p>)}
            </div>
          </article>
        ) : (
        <div className="mt-8 space-y-5">
          <label className="block text-sm font-medium">
            Title
            <input className="field mt-1.5" value={v.title} onChange={(e) => set("title", e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Slug {novo ? "(generated from title, editable)" : "(fixed after creation)"}
            <input className="field mt-1.5 font-mono text-xs" value={v.slug} disabled={!novo}
              onChange={(e) => set("slug", slugify(e.target.value))} />
          </label>
          <label className="block text-sm font-medium">
            Summary
            <input className="field mt-1.5" value={v.excerpt} onChange={(e) => set("excerpt", e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Body <span className="font-normal text-slateui">(blank line separates paragraphs; "## " makes a heading; **bold** and [links](url) supported)</span>
            <textarea className="field mt-1.5 min-h-[320px] font-mono text-sm" value={v.body}
              onChange={(e) => set("body", e.target.value)} />
          </label>

          <fieldset className="card">
            <legend className="tag px-1">cover image</legend>
            {v.image_url && <img src={v.image_url} alt={v.image_alt} className="mb-3 h-40 w-full rounded-md border border-line object-cover" />}
            <div className="flex flex-wrap items-center gap-3">
              <button type="button" className="btn-ghost !py-2 text-sm" onClick={generateCover}>
                ✦ Generate editorial cover
              </button>
              <label className="btn-ghost !py-2 cursor-pointer text-sm">
                Upload image
                <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden"
                  onChange={(e) => e.target.files?.[0] && uploadImage(e.target.files[0])} />
              </label>
              <input className="field !mt-0 flex-1 font-mono text-xs" placeholder="…or paste an image URL"
                value={v.image_url}
                onChange={(e) => set("image_url", e.target.value)} />
            </div>
            <p className="mt-2 text-xs text-slateui">Publishing is blocked until this is a verified HTTP/HTTPS raster image.</p>
            <label className="mt-3 block text-sm font-medium">
              Alt text
              <input className="field mt-1.5" value={v.image_alt} onChange={(e) => set("image_alt", e.target.value)} />
            </label>
          </fieldset>

          <div className="grid gap-5 sm:grid-cols-3">
            <label className="block text-sm font-medium">
              Category
              <select className="field mt-1.5" value={v.category} onChange={(e) => set("category", e.target.value)}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
            <label className="block text-sm font-medium">
              Tags <span className="font-normal text-slateui">(comma separated)</span>
              <input className="field mt-1.5" value={v.tags} onChange={(e) => set("tags", e.target.value)} />
            </label>
            <label className="block text-sm font-medium">
              Author
              <select className="field mt-1.5" value={v.author} onChange={(e) => set("author", e.target.value)}>
                {AUTHORS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </label>
          </div>

          <fieldset className="card">
            <legend className="tag px-1">editorial flags</legend>
            <div className="flex flex-wrap gap-x-6 gap-y-3 text-sm">
              {[["featured", "★ Featured (goes to Hero)"], ["pinned", "📌 Pin to homepage"],
                ["breaking_flag", "⚡ Breaking news"], ["editors_pick", "✦ Editor's pick"]].map(([k, l]) => (
                <label key={k} className="flex items-center gap-2">
                  <input type="checkbox" checked={!!(v as any)[k]}
                    onChange={(e) => set(k, e.target.checked ? 1 : 0)} />
                  {l}
                </label>
              ))}
            </div>
            <label className="mt-4 block text-sm font-medium">
              Schedule publication <span className="font-normal text-slateui">(UTC; leave empty to publish manually)</span>
              <input type="datetime-local" className="field mt-1.5" value={v.scheduled_at.replace(" ", "T").slice(0, 16)}
                onChange={(e) => set("scheduled_at", e.target.value ? e.target.value.replace("T", " ") + ":00" : "")} />
            </label>
            <label className="mt-4 block text-sm font-medium">
              Source URL <span className="font-normal text-slateui">(optional attribution)</span>
              <input className="field mt-1.5 font-mono text-xs" value={v.source_url}
                onChange={(e) => set("source_url", e.target.value)} />
            </label>
          </fieldset>

          <fieldset className="card">
            <legend className="tag px-1">seo preview</legend>
            <div className="rounded-md border border-line bg-black/20 p-4">
              <p className="truncate text-lg text-[#8ab4f8]">{v.seo_title || v.title || "Page title"}</p>
              <p className="truncate text-xs text-emerald-400">aionnews.cloud › article › {v.slug || "slug"}</p>
              <p className="mt-1 line-clamp-2 text-sm text-slateui">{v.seo_description || v.excerpt || "Meta description preview…"}</p>
            </div>
            <label className="mt-4 block text-sm font-medium">
              SEO title
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
        )}
      </main>
    </div>
  );
}
