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
  { label: 'Dashboard', href: '#dashboard', icon: LayoutDashboard },
  { label: 'Loop Online', href: '#loop-online', icon: Repeat2 },
  { label: 'Discovery', href: '#discovery', icon: Globe2 },
  { label: 'Agentes', href: '#agentes', icon: Bot },
  { label: 'Modelos', href: '#modelos', icon: Cpu },
  { label: 'DevOps', href: '#devops', icon: CloudCog },
  { label: 'Comercial', href: '#comercial', icon: WalletCards },
]

export const tickerItems = [
  'AION Loop online',
  'MVP conectado ao backend',
  'Discovery SEO preparado',
  'Roadmap visual em evolução',
  'Deploy contínuo preparado',
]

export const phases = [
  {
    id: 'loop-real',
    title: 'AION Loop Real',
    icon: BrainCircuit,
    status: 'Em breve',
    items: [
      'Definir objetivos',
      'Planejamento automático',
      'Quebra de tarefas',
      'Execução em sequência',
      'Autoavaliação',
      'Correção automática',
      'Relatório final',
    ],
  },
  {
    id: 'modelos',
    title: 'Central de Modelos IA',
    icon: Cpu,
    status: 'Em breve',
    items: ['OpenAI GPT', 'Claude', 'Gemini', 'Modelos locais', 'Configuração de APIs', 'Escolha de modelos'],
  },
  {
    id: 'agentes',
    title: 'Sistema de Agentes',
    icon: Bot,
    status: 'Em breve',
    items: ['Agente Master', 'Programador', 'DevOps', 'Designer', 'Auditor', 'Pesquisa', 'Memória', 'Lucro'],
  },
  {
    id: 'devops',
    title: 'Automação Dev',
    icon: CloudCog,
    status: 'Em breve',
    items: ['GitHub', 'Render', 'Vercel', 'Deploys', 'Logs', 'Monitoramento', 'Correção automática'],
  },
  {
    id: 'comercial',
    title: 'Plataforma Comercial',
    icon: WalletCards,
    status: 'Em breve',
    items: ['Usuários', 'Projetos', 'Clientes', 'Planos', 'Assinaturas', 'Pagamentos', 'Financeiro'],
  },
]

export const highlights = [
  { title: 'MVP preservado', description: 'Status, loop, histórico, logs e memória continuam conectados.', icon: Sparkles },
  { title: 'Sem features falsas', description: 'Tudo que ainda não existe aparece como “Em breve”.', icon: BrainCircuit },
]


export const discoveryTopics = [
  {
    title: 'Loops autônomos de IA',
    description: 'Conteúdo preparado para explicar como o AION planeja, executa e registra ciclos inteligentes.',
    intent: 'Educação + aquisição orgânica',
  },
  {
    title: 'Agentes inteligentes para empresas',
    description: 'Base editorial para apresentar agentes especializados, automação e ganho operacional.',
    intent: 'SaaS B2B',
  },
  {
    title: 'Automação DevOps com IA',
    description: 'Área pronta para guias sobre GitHub, Vercel, Render, monitoramento e correção assistida.',
    intent: 'Técnico + conversão',
  },
]

export const seoChecklist = [
  'Metatags essenciais configuradas',
  'Open Graph e Twitter Cards prontos',
  'Schema.org SoftwareApplication publicado',
  'robots.txt e sitemap.xml adicionados',
  'Bloco AdSense reservado sem publisher falso',
]
