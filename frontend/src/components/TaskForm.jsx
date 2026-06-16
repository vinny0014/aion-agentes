import { useState } from 'react'
export default function TaskForm({onRun,loading}){
 const [text,setText]=useState('')
 const submit=(e)=>{e.preventDefault(); if(text.trim()){onRun(text); setText('')}}
 return <form className="taskForm" onSubmit={submit}><textarea placeholder="Digite sua tarefa para o AION executar em loop..." value={text} onChange={e=>setText(e.target.value)} /><button disabled={loading}>{loading?'Executando...':'Executar Loop'}</button></form>
}
