from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from task_manager import TaskManager
from loop_agent import AionLoopAgent
from memory import MemoryStore
from schemas import TaskCreate
from config import cors_origins, allow_credentials

init_db()
app = FastAPI(title='AION Agentes', version='1.0.1')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=allow_credentials(),
    allow_methods=['*'],
    allow_headers=['*'],
)
manager = TaskManager()
agent = AionLoopAgent()
memory = MemoryStore()

@app.get('/')
def root():
    return {'message': 'AION Agentes API online', 'docs': '/docs', 'health': '/health'}

@app.get('/health')
def health():
    return {'status': 'online', 'project': 'AION Agentes'}

@app.post('/tasks')
def create_task(payload: TaskCreate):
    title = payload.title or payload.description[:60]
    return manager.create_task(title=title, description=payload.description)

@app.get('/tasks')
def list_tasks():
    return manager.list_tasks()

@app.get('/tasks/{task_id}')
def get_task(task_id: int):
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(404, 'Tarefa não encontrada')
    return {'task': task, 'steps': manager.list_steps(task_id), 'report': manager.get_report(task_id)}

@app.post('/tasks/{task_id}/run')
def run_task(task_id: int):
    if not manager.get_task(task_id):
        raise HTTPException(404, 'Tarefa não encontrada')
    return agent.run_loop(task_id)

@app.get('/tasks/{task_id}/report')
def get_report(task_id: int):
    report = manager.get_report(task_id)
    if not report:
        raise HTTPException(404, 'Relatório não encontrado')
    return report

@app.get('/logs')
def logs():
    return manager.list_logs()

@app.get('/memory')
def memories():
    return memory.list_all()
