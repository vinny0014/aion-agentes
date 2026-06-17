import {
  Bot,
  BrainCircuit,
  CloudCog,
  Cpu,
  Globe2,
  LayoutDashboard,
  Repeat2,
  Sparkles,
  WalletCards,
} from 'lucide-react'

export const navigation = [
  { label: 'Home', href: '#home' },
  { label: 'AI News', href: '#latest' },
  { label: 'Categories', href: '#categories' },
  { label: 'AI Tools', href: '#tools' },
  { label: 'Reviews', href: '#reviews' },
  { label: 'Guides', href: '#guides' },
  { label: 'Resources', href: '#resources' },
  { label: 'About', href: '#about' },
]

export const trendingItems = [
  'OpenAI launches GPT-5',
  'Google Gemini 2.0 is here',
  'Meta Llama 4 released',
  'Claude 3.5 update',
  'AI Agents are the future',
]

export const todayUpdates = [
  {
    time: '09:45 AM',
    title: 'Anthropic launches Claude 3.5 Sonnet with improved reasoning',
    accent: '#9b5cff',
    visual: 'spider',
  },
  {
    time: '08:30 AM',
    title: 'Google DeepMind releases Gemini 2.0 Flash',
    accent: '#1687ff',
    visual: 'openai',
  },
  {
    time: '07:15 AM',
    title: 'Meta introduces Llama 4 Scout and Maverick',
    accent: '#b64cff',
    visual: 'meta',
  },
  {
    time: '06:00 AM',
    title: 'Microsoft integrates Copilot deeper into Windows 11',
    accent: '#21a8ff',
    visual: 'copilot',
  },
]

export const latestNews = [
  {
    company: 'OpenAI',
    title: 'OpenAI releases new tools for developers',
    description: 'Enhanced API features and lower pricing for GPT-4.1.',
    date: 'May 25, 2026',
    read: '4 min read',
    visual: 'openai',
  },
  {
    company: 'Google',
    title: 'Gemini 2.0 Flash is now available',
    description: 'Google’s faster model with better performance.',
    date: 'May 25, 2026',
    read: '3 min read',
    visual: 'google',
  },
  {
    company: 'Meta',
    title: 'Meta Llama 4: The next generation',
    description: 'Scout and Maverick models bring major improvements.',
    date: 'May 24, 2026',
    read: '5 min read',
    visual: 'meta',
  },
  {
    company: 'Nvidia',
    title: 'Nvidia announces new AI chips',
    description: 'Blackwell architecture pushes AI performance further.',
    date: 'May 24, 2026',
    read: '4 min read',
    visual: 'nvidia',
  },
]

export const toolCards = [
  { name: 'ChatGPT', description: 'The most advanced AI assistant by OpenAI.', rating: '4.9', plan: 'Free', visual: 'chatgpt' },
  { name: 'Midjourney', description: 'Create stunning images from text prompts.', rating: '4.8', plan: 'Paid', visual: 'midjourney' },
  { name: 'Perplexity AI', description: 'AI search engine for smarter answers.', rating: '4.7', plan: 'Free', visual: 'perplexity' },
  { name: 'Runway', description: 'AI video generation made simple.', rating: '4.6', plan: 'Freemium', visual: 'runway' },
  { name: 'Claude', description: 'Anthropic’s helpful AI assistant.', rating: '4.8', plan: 'Freemium', visual: 'claude' },
]

export const topicTags = ['#OpenAI', '#GPT5', '#Gemini2', '#Claude3', '#Llama4', '#AIAgents', '#Copilot', '#AItools', '#MachineLearning', '#Nvidia']

export const mobileNav = ['Home', 'Categories', 'Tools', 'Search', 'Account']

export const phases = [
  { id: 'loop-real', title: 'AION Loop Real', icon: BrainCircuit, status: 'Em breve', items: ['Definir objetivos', 'Planejamento automático', 'Quebra de tarefas', 'Execução em sequência', 'Autoavaliação', 'Correção automática', 'Relatório final'] },
  { id: 'modelos', title: 'Central de Modelos IA', icon: Cpu, status: 'Em breve', items: ['OpenAI GPT', 'Claude', 'Gemini', 'Modelos locais', 'Configuração de APIs', 'Escolha de modelos'] },
  { id: 'agentes', title: 'Sistema de Agentes', icon: Bot, status: 'Em breve', items: ['Agente Master', 'Programador', 'DevOps', 'Designer', 'Auditor', 'Pesquisa', 'Memória', 'Lucro'] },
  { id: 'devops', title: 'Automação Dev', icon: CloudCog, status: 'Em breve', items: ['GitHub', 'Render', 'Vercel', 'Deploys', 'Logs', 'Monitoramento', 'Correção automática'] },
  { id: 'comercial', title: 'Plataforma Comercial', icon: WalletCards, status: 'Em breve', items: ['Usuários', 'Projetos', 'Clientes', 'Planos', 'Assinaturas', 'Pagamentos', 'Financeiro'] },
]

export const highlights = [
  { title: 'MVP preservado', description: 'Status, loop, histórico, logs e memória continuam conectados.', icon: Sparkles },
  { title: 'Sem features falsas', description: 'Tudo que ainda não existe aparece como “Em breve”.', icon: BrainCircuit },
]

export const discoveryTopics = [
  { title: 'Loops autônomos de IA', description: 'Conteúdo preparado para explicar como o AION planeja, executa e registra ciclos inteligentes.', intent: 'Educação + aquisição orgânica' },
  { title: 'Agentes inteligentes para empresas', description: 'Base editorial para apresentar agentes especializados, automação e ganho operacional.', intent: 'SaaS B2B' },
  { title: 'Automação DevOps com IA', description: 'Área pronta para guias sobre GitHub, Vercel, Render, monitoramento e correção assistida.', intent: 'Técnico + conversão' },
]

export const seoChecklist = [
  'Metatags essenciais configuradas',
  'Open Graph e Twitter Cards prontos',
  'Schema.org SoftwareApplication publicado',
  'robots.txt e sitemap.xml adicionados',
  'Bloco AdSense reservado sem publisher falso',
]

export const adminNavigation = [
  { label: 'Dashboard', href: '#dashboard', icon: LayoutDashboard },
  { label: 'Loop Online', href: '#loop-online', icon: Repeat2 },
  { label: 'Discovery', href: '#discovery', icon: Globe2 },
  { label: 'Agentes', href: '#agentes', icon: Bot },
  { label: 'Modelos', href: '#modelos', icon: Cpu },
  { label: 'DevOps', href: '#devops', icon: CloudCog },
  { label: 'Comercial', href: '#comercial', icon: WalletCards },
]
