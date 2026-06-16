export default function SystemPanel({logs=[], memories=[]}){
 return <section className="panel"><h2>Logs e Memória</h2><div className="miniGrid"><div><h4>Logs recentes</h4>{logs.length===0?<p className="muted">Sem logs.</p>:logs.slice(0,6).map(l=><div className="mini" key={l.id}><b>{l.level}</b><p>{l.message}</p></div>)}</div><div><h4>Memória</h4>{memories.length===0?<p className="muted">Sem memória.</p>:memories.slice(0,6).map(m=><div className="mini" key={m.id}><b>{m.memory_key}</b><p>{m.memory_value}</p></div>)}</div></div></section>
}
