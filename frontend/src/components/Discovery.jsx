import { BadgeDollarSign, CheckCircle2, Globe2, SearchCheck } from 'lucide-react'
import { discoveryTopics, seoChecklist } from '../data/dashboard.js'

export function Discovery() {
  return (
    <section className="discoverySection" id="discovery">
      <div className="sectionHeading">
        <span className="eyebrow"><Globe2 size={15} /> AION DISCOVERY</span>
        <h2>Base SEO e aquisição orgânica preparada</h2>
        <p>
          AION agora possui fundação técnica para descoberta em buscadores e estrutura visual para evoluir
          conteúdo, páginas públicas e monetização sem criar promessas falsas.
        </p>
      </div>

      <div className="discoveryGrid">
        <article className="seoPanel primarySeoPanel">
          <div className="panelTitle">
            <h3>SEO técnico</h3>
            <SearchCheck size={20} />
          </div>
          <ul className="seoChecklist">
            {seoChecklist.map((item) => (
              <li key={item}><CheckCircle2 size={16} />{item}</li>
            ))}
          </ul>
        </article>

        <article className="seoPanel adsensePanel">
          <div className="panelTitle">
            <h3>AdSense</h3>
            <BadgeDollarSign size={20} />
          </div>
          <p>
            Área reservada para monetização futura. O código do Google AdSense deve ser ativado somente
            após aprovação da conta e configuração real do publisher ID.
          </p>
          <span className="comingSoonBadge">Preparado • aguardando conta</span>
        </article>
      </div>

      <div className="topicGrid" aria-label="Temas de descoberta do AION">
        {discoveryTopics.map((topic) => (
          <article className="topicCard" key={topic.title}>
            <small>{topic.intent}</small>
            <h3>{topic.title}</h3>
            <p>{topic.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
