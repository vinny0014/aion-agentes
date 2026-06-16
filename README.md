# AION Agentes

Plataforma funcional de Engenharia de Loops para Agentes Inteligentes.

## Recursos entregues

- Backend FastAPI
- Frontend React + Vite
- Banco SQLite local, preparado para PostgreSQL no futuro
- Painel para criar tarefas, executar loop, acompanhar etapas, histórico, relatório, logs e memória
- Rotas obrigatórias: `/`, `/health`, `/tasks`, `/tasks/{id}`, `/tasks/{id}/run`, `/tasks/{id}/report`, `/logs`, `/memory`
- Configurações de deploy para Render, Railway e Vercel

## Rodar localmente

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Teste:

```bash
curl http://localhost:8000/health
```

Resposta esperada:

```json
{"status":"online","project":"AION Agentes"}
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5173

Se o backend estiver publicado, crie `frontend/.env`:

```bash
VITE_API_URL=https://SUA-API.onrender.com
```

## Testes

```bash
cd backend
source .venv/bin/activate
pytest
```

```bash
cd frontend
npm install
npm run build
```

## Deploy

### Backend no Render

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variável recomendada: `AION_ALLOWED_ORIGINS=https://SEU-FRONTEND.vercel.app`

### Frontend no Vercel

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Variável obrigatória: `VITE_API_URL=https://SUA-API.onrender.com`

## Loop AION

O agente implementa as funções principais:

- `receive_task()`
- `create_plan()`
- `execute_step()`
- `validate_step()`
- `fix_error()`
- `save_memory()`
- `generate_report()`
- `run_loop()`

## Status

Projeto auditado, corrigido, testado localmente e empacotado para deploy.
