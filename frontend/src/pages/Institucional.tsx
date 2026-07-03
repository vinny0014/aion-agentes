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

export function Privacidade() {
  return (
    <Pagina tag="legal" titulo="Política de Privacidade">
      <p>O AION AGENTES coleta apenas os dados necessários para operar a plataforma: nome e e-mail no cadastro, e as mensagens enviadas pelo formulário de contato.</p>
      <p>Senhas são armazenadas exclusivamente com hash criptográfico (bcrypt) — nem a equipe tem acesso a elas. Tokens de sessão expiram automaticamente e podem ser revogados.</p>
      <p>Não vendemos nem compartilhamos dados pessoais com terceiros. Dados de navegação podem ser usados de forma agregada e anônima para melhorar o portal.</p>
      <p>Você pode solicitar a exclusão da sua conta e dos seus dados a qualquer momento pela página de Contato. Esta política pode ser atualizada; a versão vigente estará sempre nesta página.</p>
    </Pagina>
  );
}

export function Termos() {
  return (
    <Pagina tag="legal" titulo="Termos de Uso">
      <p>Ao usar o AION AGENTES você concorda com estes termos. O portal oferece conteúdo informativo sobre inteligência artificial, produzido com apoio de agentes de IA e supervisão humana.</p>
      <p>O conteúdo é fornecido "como está", sem garantias de exatidão ou adequação a finalidades específicas, e não constitui aconselhamento profissional.</p>
      <p>É proibido usar a plataforma para fins ilegais, tentar acessar áreas restritas sem autorização ou sobrecarregar deliberadamente os serviços.</p>
      <p>O conteúdo publicado pode ser citado com atribuição e link para o artigo original. Estes termos podem ser revisados periodicamente.</p>
    </Pagina>
  );
}

export function Contato() {
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
    <Pagina tag="fale conosco" titulo="Contato">
      <p>Dúvidas, sugestões de pauta ou parcerias? Envie sua mensagem.</p>
      <form onSubmit={enviar} className="mt-2 max-w-md space-y-4 text-ink">
        <label className="block text-sm font-medium">Nome
          <input className="field mt-1.5" required minLength={2} value={v.name}
            onChange={(e) => setV({ ...v, name: e.target.value })} />
        </label>
        <label className="block text-sm font-medium">E-mail
          <input className="field mt-1.5" type="email" required value={v.email}
            onChange={(e) => setV({ ...v, email: e.target.value })} />
        </label>
        <label className="block text-sm font-medium">Mensagem
          <textarea className="field mt-1.5 min-h-[120px]" required minLength={5} value={v.message}
            onChange={(e) => setV({ ...v, message: e.target.value })} />
        </label>
        {ok && <p className="rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">{ok}</p>}
        {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300">{erro}</p>}
        <button className="btn-primary" disabled={enviando}>{enviando ? "Enviando…" : "Enviar mensagem"}</button>
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
      {itens === null ? <p className="font-mono text-sm">carregando…</p>
        : itens.length === 0 ? (
          <p>Nenhuma {tipo === "categorias" ? "categoria" : "tag"} ainda — elas aparecem aqui quando artigos publicados as utilizam.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {itens.map((i) => (
              <a key={i[chave]} href={`/conteudos?${tipo === "categorias" ? "categoria" : "tag"}=${encodeURIComponent(i[chave])}`}
                className="chip">
                {i[chave]} <span className="font-mono text-xs text-slateui">({i.total})</span>
              </a>
            ))}
          </div>
        )}
    </Pagina>
  );
}
