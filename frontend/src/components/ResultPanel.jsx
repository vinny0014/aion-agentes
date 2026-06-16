export default function ResultPanel({report}){return <section className="panel"><h2>Relatório Final</h2><pre>{report || 'Aguardando execução do primeiro loop.'}</pre></section>}
