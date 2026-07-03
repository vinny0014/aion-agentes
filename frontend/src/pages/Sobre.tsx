import { Nav } from "./Landing";

export default function Sobre() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-14">
        <p className="tag mb-3">institucional</p>
        <h1 className="font-display text-4xl font-bold tracking-tight">Sobre o AION AGENTES</h1>
        <div className="mt-6 space-y-5 text-slateui leading-relaxed">
          <p>
            O AION AGENTES é um portal de inteligência artificial construído sobre uma ideia
            simples: um veículo de conteúdo pode ser operado, do rascunho à publicação, por uma
            equipe de agentes de IA com responsabilidades bem definidas — sob supervisão humana.
          </p>
          <p>
            A plataforma reúne um pipeline de produção diária de conteúdo (fila, agendador e
            templates), um painel administrativo completo e uma API REST preparada para conectar
            os principais provedores de IA do mercado: OpenAI, Anthropic, OpenRouter e Gemini.
          </p>
          <p>
            Nove agentes formam a equipe: CEO Master, Developer, QA, Content, SEO, GitHub,
            Deploy, Monitor e Cost Guard. Cada um cobre uma etapa da operação, do código ao
            controle de custos.
          </p>
          <p>
            O projeto nasceu preparado para produção: autenticação com JWT e refresh token,
            senhas com hash, segredos fora do banco, SEO técnico completo e arquitetura pronta
            para migrar de SQLite para PostgreSQL quando a escala pedir.
          </p>
        </div>
      </main>
    </div>
  );
}
