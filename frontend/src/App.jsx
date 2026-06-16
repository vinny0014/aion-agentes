import { useEffect, useMemo, useState } from 'react'
import { Footer, Sidebar, Topbar } from './components/DashboardShell.jsx'
import { Hero, Metrics } from './components/DashboardCards.jsx'
import { HistoryPanel, ResultPanel, SystemPanel, TaskComposer, Timeline } from './components/LoopWorkbench.jsx'
import { Discovery } from './components/Discovery.jsx'
import { Roadmap } from './components/Roadmap.jsx'
import { api, API_URL } from './services/api.js'

function isBackendOnline(status) {
  return ['ok', 'online', 'healthy'].includes(String(status).toLowerCase())
}

export default function App() {
  const [health, setHealth] = useState('verificando')
  const [tasks, setTasks] = useState([])
  const [steps, setSteps] = useState([])
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [memories, setMemories] = useState([])
  const [menuOpen, setMenuOpen] = useState(false)

  const online = isBackendOnline(health)
  const apiUrl = useMemo(() => API_URL, [])

  async function loadDashboardData() {
    try {
      const [healthResponse, taskList, logList, memoryList] = await Promise.all([
        api.health(),
        api.tasks(),
        api.logs(),
        api.memory(),
      ])

      setHealth(healthResponse.status)
      setTasks(Array.isArray(taskList) ? taskList : [])
      setLogs(Array.isArray(logList) ? logList : [])
      setMemories(Array.isArray(memoryList) ? memoryList : [])
    } catch (error) {
      setHealth('offline')
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  async function runLoop(text) {
    setLoading(true)

    try {
      const created = await api.createTask(text)
      const result = await api.runTask(created.id)
      setSteps(result.steps || [])
      setReport(result.report || 'Loop finalizado sem relatório detalhado.')
      await loadDashboardData()
    } catch (error) {
      setReport(`Erro ao executar loop: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="appShell">
      <Sidebar open={menuOpen} />
      <main className="dashboard">
        <Topbar menuOpen={menuOpen} onToggleMenu={() => setMenuOpen((current) => !current)} online={online} />
        <Hero apiUrl={apiUrl} />
        <Metrics health={health} loading={loading} tasksCount={tasks.length} />

        <section id="loop-online" className="workbench">
          <TaskComposer onRun={runLoop} loading={loading} />
          <HistoryPanel tasks={tasks} />
        </section>

        <section className="contentGrid">
          <Timeline steps={steps} />
          <ResultPanel report={report} />
          <SystemPanel logs={logs} memories={memories} />
        </section>

        <Discovery />
        <Roadmap />
        <Footer />
      </main>
    </div>
  )
}
