import { Database, History, Play, TerminalSquare, Zap } from 'lucide-react'
import { useState } from 'react'

export function TaskComposer({ onRun, loading }) {
  const [text, setText] = useState('')

  function submit(event) {
    event.preventDefault()
    if (!text.trim()) return
    onRun(text.trim())
    setText('')
  }

  return (
    <form className="composer" onSubmit={submit}>
      <div>
        <span className="eyebrow"><Zap size={14} /> MVP FUNCIONANDO</span>
        <h2>Executar Loop Autônomo</h2>
        <p>Descreva uma tarefa e acompanhe planejamento, execução, histórico, logs e memória do AION.</p>
      </div>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Ex.: Analise uma ideia de produto, gere um plano e registre aprendizados..."
      />
      <button disabled={loading} type="submit">
        <Play size={18} />{loading ? 'Executando loop...' : 'Executar Loop'}
      </button>
    </form>
  )
}

export function Timeline({ steps }) {
  return (
    <section className="glassPanel">
      <div className="panelTitle">
        <h2>Etapas do Loop</h2>
        <span>{steps.length || 0} etapas</span>
      </div>
      {steps.length === 0 ? (
        <p className="empty">Nenhuma etapa executada ainda.</p>
      ) : (
        <div className="timeline">
          {steps.map((step) => (
            <div className="timelineItem" key={step.id}>
              <span>{step.step_order}</span>
              <div>
                <strong>{step.title}</strong>
                <small>{step.status}</small>
                <p>{step.details}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export function HistoryPanel({ tasks }) {
  return (
    <section className="glassPanel">
      <div className="panelTitle">
        <h2>Histórico</h2>
        <History size={18} />
      </div>
      {tasks.length === 0 ? (
        <p className="empty">Sem tarefas ainda.</p>
      ) : (
        tasks.slice(0, 7).map((task) => (
          <article className="historyItem" key={task.id}>
            <strong>#{task.id} {task.title}</strong>
            <span>{task.status}</span>
            <p>{task.description}</p>
          </article>
        ))
      )}
    </section>
  )
}

export function ResultPanel({ report }) {
  return (
    <section className="glassPanel">
      <div className="panelTitle">
        <h2>Relatório Final</h2>
        <TerminalSquare size={18} />
      </div>
      <pre>{report || 'Aguardando execução do primeiro loop.'}</pre>
    </section>
  )
}

export function SystemPanel({ logs, memories }) {
  return (
    <section className="glassPanel wide">
      <div className="panelTitle">
        <h2>Logs e Memória</h2>
        <Database size={18} />
      </div>
      <div className="systemGrid">
        <div>
          {logs.length === 0 ? (
            <p className="empty">Sem logs.</p>
          ) : (
            logs.slice(0, 5).map((log) => (
              <article className="miniRow" key={log.id}>
                <b>{log.level}</b>
                <p>{log.message}</p>
              </article>
            ))
          )}
        </div>
        <div>
          {memories.length === 0 ? (
            <p className="empty">Sem memória.</p>
          ) : (
            memories.slice(0, 5).map((memory) => (
              <article className="miniRow" key={memory.id}>
                <b>{memory.memory_key}</b>
                <p>{memory.memory_value}</p>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  )
}
