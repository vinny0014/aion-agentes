import { Code2, Menu, Search, Sparkles, X, Zap } from 'lucide-react'
import { navigation, tickerItems } from '../data/dashboard.js'

export function StatusPill({ online }) {
  return (
    <span className={`statusPill ${online ? 'online' : 'offline'}`}>
      <span aria-hidden="true" />
      {online ? 'Backend online' : 'Backend offline'}
    </span>
  )
}

export function Sidebar({ open }) {
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand">
        <div className="logoMark">A</div>
        <div>
          <strong>AION</strong>
          <small>AI AGENTES OS</small>
        </div>
      </div>

      <nav aria-label="Navegação principal">
        {navigation.map((item, index) => {
          const Icon = item.icon
          return (
            <a className={index === 0 ? 'active' : ''} href={item.href} key={item.label}>
              <Icon size={17} />
              {item.label}
            </a>
          )
        })}
      </nav>

      <div className="sidebarCard">
        <Sparkles size={18} />
        <strong>Produção SaaS</strong>
        <p>FastAPI + React conectados para o MVP atual.</p>
      </div>
    </aside>
  )
}

export function Topbar({ menuOpen, onToggleMenu, online }) {
  return (
    <header className="topbar">
      <button className="menuButton" onClick={onToggleMenu} type="button" aria-label="Abrir navegação">
        {menuOpen ? <X /> : <Menu />}
      </button>

      <div className="ticker" aria-label="Atualizações do AION">
        <Zap size={16} />
        <b>TRENDING NOW</b>
        {tickerItems.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>

      <div className="actions">
        <Search size={20} />
        <StatusPill online={online} />
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer>
      <Code2 size={16} /> AION Agentes • Plataforma online e operacional
    </footer>
  )
}
