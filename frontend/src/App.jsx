import {
  ArrowRight,
  Bell,
  Bot,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleUserRound,
  Grid2X2,
  Home,
  Menu,
  MoonStar,
  Search,
  Shapes,
  Sparkles,
  Star,
  Sun,
  Zap,
} from 'lucide-react'
import { latestNews, mobileNav, navigation, todayUpdates, toolCards, topicTags, trendingItems } from './data/news.js'

function Logo() {
  return (
    <a className="brandLogo" href="#home" aria-label="AION AI News OS">
      <span className="aionMark">A</span>
      <span><strong>AION</strong><small>AI NEWS OS</small></span>
    </a>
  )
}

function BrandVisual({ type, compact = false }) {
  return <div className={`brandVisual ${type} ${compact ? 'compact' : ''}`}><span /></div>
}

function RobotPortrait() {
  return (
    <div className="robotPortrait" aria-hidden="true">
      <img src="/aion-robot-hero.svg" alt="" />
    </div>
  )
}

function Header() {
  return (
    <header className="newsHeader" id="home">
      <Logo />
      <nav className="desktopNav" aria-label="Primary navigation">
        {navigation.map((item, index) => (
          <a className={index === 0 ? 'active' : ''} href={item.href} key={item.label}>
            {item.label}{item.label === 'Categories' && <ChevronDown size={13} />}
          </a>
        ))}
      </nav>
      <div className="headerActions">
        <Search size={21} />
        <Sun size={19} />
        <button>Subscribe</button>
      </div>
      <button className="mobileMenu" aria-label="Open menu"><Menu size={24} /></button>
    </header>
  )
}

function TrendingBar({ mobile = false }) {
  return (
    <section className={`trendingBar ${mobile ? 'mobileTrend' : ''}`}>
      <div className="trendLabel"><Zap size={15} />{mobile ? 'TRENDING:' : 'TRENDING NOW'}</div>
      <div className="trendTrack">
        {trendingItems.map((item) => <span key={item}>{item}</span>)}
      </div>
      <div className="trendControls"><button><ChevronLeft size={15} /></button><button><ChevronRight size={15} /></button></div>
    </section>
  )
}

function HeroStory({ mobile = false }) {
  return (
    <article className={`heroStory ${mobile ? 'mobileHero' : ''}`}>
      <div className="storyContent">
        <div className="storyBadges"><span>FEATURED</span><b>AI BREAKING NEWS</b></div>
        <h1>OpenAI Unveils GPT-5: More Powerful, Faster and Smarter Than Ever</h1>
        {!mobile && <p>OpenAI officially announces GPT-5 with major advancements in reasoning, coding, and multimodal understanding.</p>}
        <div className="storyMeta">
          {!mobile && <span className="authorIcon"><Bot size={18} /></span>}
          {!mobile && <div><strong>AION AI News Team</strong><small>May 25, 2026&nbsp;&nbsp;•&nbsp;&nbsp;5 min read</small></div>}
          <a href="#story">Read Full Story <ArrowRight size={16} /></a>
        </div>
      </div>
      <RobotPortrait />
    </article>
  )
}

function TodayInAI({ compact = false }) {
  return (
    <aside className="sidePanel todayPanel">
      <div className="panelHeading"><h2>TODAY IN AI</h2><span className="liveBadge">● LIVE</span></div>
      <div className="updateList">
        {todayUpdates.map((update) => (
          <article className="updateItem" key={update.title}>
            <BrandVisual type={update.visual} compact />
            <div><time>{update.time}</time><p>{update.title}</p></div>
            <i style={{ background: update.accent }} />
          </article>
        ))}
      </div>
      <a className="panelLink" href="#updates">View All Updates <ArrowRight size={14} /></a>
    </aside>
  )
}

function Newsletter() {
  return (
    <aside className="sidePanel newsletterPanel">
      <h2>NEWSLETTER</h2>
      <p>Get the top AI news, tools, and insights delivered to your inbox.</p>
      <form><input placeholder="Enter your email" /><button>Subscribe</button></form>
      <small>◎ No spam. Unsubscribe anytime.</small>
    </aside>
  )
}

function TrendingTopics() {
  return (
    <aside className="sidePanel topicsPanel">
      <h2>TRENDING TORCS</h2>
      <div className="topicCloud">{topicTags.map((tag) => <span key={tag}>{tag}</span>)}</div>
      <a className="panelLink" href="#topics">View All Topics <ArrowRight size={14} /></a>
    </aside>
  )
}

function LatestNews() {
  return (
    <section className="contentPanel latestPanel" id="latest">
      <div className="sectionTitle"><h2>LATEST AI NEWS</h2><a href="#latest">View All News <ArrowRight size={14} /></a></div>
      <div className="newsGrid">
        {latestNews.map((news) => (
          <article className="newsCard" key={news.title}>
            <BrandVisual type={news.visual} />
            <div className="newsCardBody"><small>{news.company}</small><h3>{news.title}</h3><p>{news.description}</p><time>{news.date}&nbsp;&nbsp;•&nbsp;&nbsp;{news.read}</time></div>
          </article>
        ))}
      </div>
    </section>
  )
}

function ToolsHub() {
  return (
    <section className="contentPanel toolsPanel" id="tools">
      <div className="sectionTitle"><h2>AI TOOLS HUB</h2><a href="#tools">View All Tools <ArrowRight size={14} /></a></div>
      <div className="toolsGrid">
        {toolCards.map((tool) => (
          <article className="toolCard" key={tool.name}>
            <BrandVisual type={tool.visual} compact />
            <div><h3>{tool.name}</h3><p>{tool.description}</p></div>
            <div className="toolFooter"><span><Star size={15} fill="currentColor" />{tool.rating}</span><small>{tool.plan} <ArrowRight size={13} /></small></div>
          </article>
        ))}
      </div>
    </section>
  )
}

function MobilePreview() {
  return (
    <aside className="phoneMock" aria-label="Mobile layout preview">
      <div className="phoneScreen">
        <div className="phoneStatus"><span>9:41</span><span>▮▮ ◓ ▰</span></div>
        <div className="phoneHeader"><Logo /><Menu size={21} /></div>
        <TrendingBar mobile />
        <HeroStory mobile />
        <TodayInAI compact />
        <section className="phoneLatest"><div className="sectionTitle"><h2>LATEST NEWS</h2><a>View All</a></div><article><BrandVisual type="openai" compact /><div><small>OPENAI</small><h3>OpenAI releases new tools for developers</h3><time>May 25, 2026 • 4 min read</time></div></article></section>
        <nav className="bottomNav">{mobileNav.map((item, index) => <a className={index === 0 ? 'active' : ''} key={item}>{index === 0 ? <Home /> : index === 1 ? <Grid2X2 /> : index === 2 ? <Shapes /> : index === 3 ? <Search /> : <CircleUserRound />}<span>{item}</span></a>)}</nav>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <main className="newsShell">
      <section className="siteFrame">
        <Header />
        <TrendingBar />
        <div className="leadGrid">
          <div className="mainColumn"><HeroStory /><LatestNews /><ToolsHub /></div>
          <div className="sideColumn"><TodayInAI /><Newsletter /><TrendingTopics /></div>
        </div>
      </section>
      <MobilePreview />
      <button className="themeFloat" aria-label="Theme"><MoonStar size={18} /></button>
      <button className="notifyFloat" aria-label="Notifications"><Bell size={18} /></button>
    </main>
  )
}
