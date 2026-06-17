import { Activity, CheckCircle2, ChevronRight, Gauge, Rocket, ShieldCheck } from 'lucide-react'

export function MetricCard({ icon: Icon, label, value, note }) {
  return (
    <article className="metricCard">
      <div className="metricIcon"><Icon size={20} /></div>
      <p>{label}</p>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

export function Hero({ apiUrl }) {
  return (
    <section className="hero" id="dashboard">
      <div className="heroCopy">
        <span className="eyebrow"><Rocket size={15} /> PLATAFORMA AION</span>
        <h1>Centro premium de IA para loops, agentes e automação.</h1>
        <p>
          Dashboard profissional inspirado no mockup oficial, preservando o MVP funcional e preparando
          todas as próximas fases como módulos “Em breve”.
        </p>
        <div className="heroActions">
          <a href="#loop-online">Abrir Loop <ChevronRight size={16} /></a>
          <span>API: {apiUrl}</span>
        </div>
      </div>
      <div className="heroOrb" aria-hidden="true">
        <div><span className="orbCore">AI</span><small>CORE</small></div>
      </div>
    </section>
  )
}

export function Metrics({ health, loading, tasksCount }) {
  return (
    <section className="metrics" aria-label="Métricas do sistema">
      <MetricCard icon={Activity} label="Status do Backend" value={health} note="Render FastAPI" />
      <MetricCard icon={CheckCircle2} label="Tarefas Executadas" value={tasksCount} note="Histórico preservado" />
      <MetricCard icon={Gauge} label="Modo" value="Produção" note="Vercel + API" />
      <MetricCard icon={ShieldCheck} label="Loop Online" value={loading ? 'Executando' : 'Pronto'} note="MVP operacional" />
    </section>
  )
}
