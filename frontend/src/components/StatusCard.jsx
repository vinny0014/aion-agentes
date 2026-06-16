export default function StatusCard({title,value,small}){return <div className="card"><p>{title}</p><h3>{value}</h3>{small&&<span>{small}</span>}</div>}
