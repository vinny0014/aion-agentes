# Checklist de Produção — AION Agentes

## Backend Render/Railway

1. Criar novo serviço web.
2. Conectar repositório GitHub.
3. Root directory: `backend`.
4. Build command: `pip install -r requirements.txt`.
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
6. Configurar `AION_ALLOWED_ORIGINS` com a URL do frontend.
7. Validar `/health`.

## Frontend Vercel

1. Criar novo projeto.
2. Root directory: `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Configurar `VITE_API_URL` com a URL pública do backend.
6. Validar painel online.

## Critério de aceite

- Backend online.
- Frontend online.
- `GET /health` retorna `{ "status": "online", "project": "AION Agentes" }`.
- Criar tarefa funciona.
- Executar loop funciona.
- Histórico, relatório, logs e memória aparecem no painel.
