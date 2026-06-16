import { useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import StatusCard from './components/StatusCard.jsx'
import TaskForm from './components/TaskForm.jsx'
import LoopTimeline from './components/LoopTimeline.jsx'
import ResultPanel from './components/ResultPanel.jsx'
import TaskHistory from './components/TaskHistory.jsx'
import SystemPanel from './components/SystemPanel.jsx'
import { api } from './services/api.js'

export default function App(){
 const [health,setHealth]=useState('verificando')
 const [tasks,setTasks]=useState([])
 const [steps,setSteps]=useState([])
 const [report,setReport]=useState('')
 const [loading,setLoading]=useState(false)
 const [logs,setLogs]=useState([])
 const [memories,setMemories]=useState([])
 async function load(){
  try{const h=await api.health(); setHealth(h.status); const t=await api.tasks(); setTasks(t); setLogs(await api.logs()); setMemories(await api.memory())}catch(e){setHealth('offline')}
 }
 useEffect(()=>{load()},[])
 async function run(text){
  setLoading(true)
  try{const created=await api.createTask(text); const result=await api.runTask(created.id); setSteps(result.steps); setReport(result.report); await load()}catch(e){setReport('Erro ao executar loop: '+e.message)}finally{setLoading(false)}
 }
 return <main><Header/><section className="grid"><StatusCard title="Status do Backend" value={health}/><StatusCard title="Tarefas Executadas" value={tasks.length}/><StatusCard title="Modo" value="Produção pronta" small="FastAPI + React"/></section><TaskForm onRun={run} loading={loading}/><section className="content"><div><LoopTimeline steps={steps}/><ResultPanel report={report}/><SystemPanel logs={logs} memories={memories}/></div><TaskHistory tasks={tasks}/></section></main>
}
