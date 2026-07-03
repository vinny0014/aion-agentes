import { Link } from "react-router-dom";

const AGENTES = [
  { slug: "ceo-master", nome: "CEO Master", papel: "orquestração", linha: "prioriza fila · aprova entregas" },
  { slug: "content", nome: "Content", papel: "conteúdo", linha: "3 artigos na fila de hoje" },
  { slug: "seo", nome: "SEO", papel: "otimização", linha: "sitemap atualizado · schema ok" },
  { slug: "developer", nome: "Developer", papel: "engenharia", linha: "build verde · 11 testes ok" },
  { slug: "qa", nome: "QA", papel: "qualidade", linha: "cobertura de fluxos críticos" },
  { slug: "monitor", nome: "Monitor", papel: "observabilidade", linha: "health: ok · uptime 100%" },
  { slug: "github", nome: "GitHub", papel: "versionamento", linha: "branch main protegida" },
  { slug: "deploy", nome: "Deploy", papel: "devops", linha: "vercel + render preparados" },
  { slug: "cost-guard", nome: "Cost Guard", papel: "custos", linha: "orçamento de API sob controle" },
];

export function Nav() {
  return (
    <nav className="glass-nav"><div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
      <Link to="/" className="font-display text-xl font-bold tracking-tight">
        AION<span className="text-ultra">·</span>AGENTES
      </Link>
      <div className="flex items-center gap-2 text-sm">
        <Link to="/conteudos" className="px-3 py-2 text-slateui hover:text-ink">Conteúdos</Link>
        <Link to="/sobre" className="px-3 py-2 text-slateui hover:text-ink">Sobre</Link>
        <Link to="/login" className="px-3 py-2 text-slateui hover:text-ink">Entrar</Link>
        <Link to="/cadastro" className="btn-primary !px-4 !py-2 text-sm">Criar conta</Link>
      </div></div>
    </nav>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Nav />

      <header className="relative mx-auto max-w-6xl overflow-visible px-6 pb-16 pt-12 md:pt-20">
        <div className="orb h-64 w-64 bg-ultra/25" style={{ top: "-40px", right: "8%" }} />
        <div className="orb h-52 w-52 bg-signal/25" style={{ top: "120px", right: "24%", animationDelay: "-4s" }} />
        <p className="rise tag mb-4 inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/70 px-3 py-1.5 backdrop-blur">
          <span className="status-dot inline-block h-1.5 w-1.5 rounded-full bg-signal" />
          portal de inteligência artificial · publicação diária
        </p>
        <h1 className="rise rise-1 max-w-3xl font-display text-4xl font-bold leading-tight tracking-tight md:text-6xl">
          Um portal de IA operado por uma equipe de{" "}
          <span className="grad-text">agentes inteligentes</span>.
        </h1>
        <p className="rise rise-2 mt-5 max-w-2xl text-lg text-slateui">
          Notícias, guias e análises sobre inteligência artificial, produzidos todos os dias
          por um pipeline de agentes — do conteúdo ao SEO, do deploy ao monitoramento.
        </p>
        <div className="rise rise-3 mt-8 flex flex-wrap gap-3">
          <Link to="/cadastro" className="btn-primary">Começar agora</Link>
          <Link to="/conteudos" className="px-3 py-2 text-slateui hover:text-ink">Conteúdos</Link>
        <Link to="/sobre" className="btn-ghost">Como funciona</Link>
        </div>
      </header>

      {/* Quadro de operação — elemento assinatura */}
      <section aria-label="Quadro de operação dos agentes" className="border-y border-ink/10 bg-white/60 backdrop-blur-sm">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Quadro de operação</h2>
            <span className="font-mono text-xs text-signal">
              <span className="status-dot mr-1.5 inline-block h-2 w-2 rounded-full bg-signal align-middle" />
              equipe em atividade
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {AGENTES.map((a) => (
              <div key={a.slug} className="card card-hover !p-4">
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold">{a.nome}</span>
                  <span className="tag">{a.papel}</span>
                </div>
                <p className="mt-2 font-mono text-xs text-slateui">
                  <span className="text-signal">▸</span> {a.linha}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid gap-6 md:grid-cols-3">
          <div className="card card-hover">
            <p className="tag mb-2">conteúdo</p>
            <h3 className="font-display text-lg font-bold">Publicação diária</h3>
            <p className="mt-2 text-sm text-slateui">
              Fila, agendador e templates prontos para produzir artigos todos os dias,
              conectáveis a OpenAI, Anthropic, OpenRouter e Gemini.
            </p>
          </div>
          <div className="card card-hover">
            <p className="tag mb-2">plataforma</p>
            <h3 className="font-display text-lg font-bold">Painel completo</h3>
            <p className="mt-2 text-sm text-slateui">
              Usuários, agentes, conteúdo, tarefas, logs, memória e configurações —
              tudo administrável em um só lugar.
            </p>
          </div>
          <div className="card card-hover">
            <p className="tag mb-2">base</p>
            <h3 className="font-display text-lg font-bold">Pronto para escalar</h3>
            <p className="mt-2 text-sm text-slateui">
              API REST documentada, autenticação com JWT e refresh token, SQLite hoje,
              PostgreSQL amanhã.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-ink/10">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-8 text-sm text-slateui">
          <span className="font-display font-bold text-ink">AION·AGENTES</span>
          <div className="flex gap-4 text-xs">
            <Link to="/categorias" className="hover:text-ink">Categorias</Link>
            <Link to="/tags" className="hover:text-ink">Tags</Link>
            <Link to="/privacidade" className="hover:text-ink">Privacidade</Link>
            <Link to="/termos" className="hover:text-ink">Termos</Link>
            <Link to="/contato" className="hover:text-ink">Contato</Link>
          </div>
          <span className="font-mono text-xs">© {new Date().getFullYear()} · feito por agentes, supervisionado por humanos</span>
        </div>
      </footer>
    </div>
  );
}
