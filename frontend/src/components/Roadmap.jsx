import { Layers3 } from 'lucide-react'
import { phases } from '../data/dashboard.js'

function PhaseCard({ phase }) {
  const Icon = phase.icon
  return (
    <article className="phaseCard" id={phase.id}>
      <div className="phaseTop">
        <div className="metricIcon"><Icon size={19} /></div>
        <span>{phase.status}</span>
      </div>
      <h3>{phase.title}</h3>
      <div className="chipCloud">
        {phase.items.map((item) => <small key={item}>{item}</small>)}
      </div>
    </article>
  )
}

export function Roadmap() {
  return (
    <section className="phaseSection">
      <div className="sectionHeading">
        <span className="eyebrow"><Layers3 size={15} /> ROADMAP VISUAL</span>
        <h2>Próximas fases preparadas</h2>
        <p>Sem simular funcionalidades prontas: todos os módulos futuros aparecem com status claro “Em breve”.</p>
      </div>
      <div className="phaseGrid">
        {phases.map((phase) => <PhaseCard key={phase.title} phase={phase} />)}
      </div>
    </section>
  )
}
