# AION Agentes — Guia de Deploy Completo

## Arquitetura de Produção

```
[Vercel] Frontend React/Vite
    ↓ VITE_API_URL
[Render] Backend FastAPI + SQLite
```

---

## PASSO 1 — Subir código no GitHub

```bash
cd aion-agentes
git init
git add .
git commit -m "AION Agentes - deploy inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/aion-agentes.git
git push -u origin main
```

---

## PASSO 2 — Backend no Render (gratuito)

1. Acesse https://render.com → New → Web Service
2. Connect ao repositório GitHub
3. Configure:
   - **Name:** `aion-agentes-api`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Em **Environment Variables**, adicione:
   - `AION_ALLOWED_ORIGINS` = `*`  *(depois mudar para a URL do Vercel)*
   - `AION_DB_PATH` = `/tmp/aion.db`
5. Clique **Create Web Service**
6. Aguarde o deploy (~2 min)
7. **Copie a URL gerada**, ex: `https://aion-agentes-api.onrender.com`

### ✅ Teste imediato:
```bash
curl https://aion-agentes-api.onrender.com/health
# Resposta esperada: {"status":"online","project":"AION Agentes"}
```

---

## PASSO 3 — Frontend no Vercel (gratuito)

1. Acesse https://vercel.com → New Project
2. Import do repositório GitHub
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Em **Environment Variables**, adicione:
   - `VITE_API_URL` = `https://aion-agentes-api.onrender.com`
     *(URL exata do Render — sem barra no final)*
5. Clique **Deploy**
6. **Copie a URL gerada**, ex: `https://aion-agentes.vercel.app`

---

## PASSO 4 — Atualizar CORS no Render

Após ter a URL do Vercel:

1. Acesse o serviço no Render → Environment
2. Mude `AION_ALLOWED_ORIGINS` de `*` para:
   ```
   https://aion-agentes.vercel.app
   ```
3. Salve → Render fará redeploy automático

---

## PASSO 5 — Validação final

### Backend — todas as rotas:
```bash
BASE=https://aion-agentes-api.onrender.com

# GET /
curl $BASE/

# GET /health
curl $BASE/health

# GET /tasks
curl $BASE/tasks

# POST /tasks
curl -X POST $BASE/tasks \
  -H "Content-Type: application/json" \
  -d '{"description":"Criar relatório de vendas Q2"}'

# POST /tasks/1/run
curl -X POST $BASE/tasks/1/run

# GET /tasks/1
curl $BASE/tasks/1

# GET /tasks/1/report
curl $BASE/tasks/1/report

# GET /logs
curl $BASE/logs

# GET /memory
curl $BASE/memory
```

### Frontend:
- [ ] Painel abre na URL do Vercel
- [ ] Status mostra "online"
- [ ] Campo de tarefa disponível
- [ ] Botão "Executar Loop" funciona
- [ ] Timeline de etapas aparece
- [ ] Relatório é exibido
- [ ] Histórico de tarefas lista corretamente
- [ ] Aba Logs mostra registros
- [ ] Aba Memória mostra entradas

---

## Alternativa: Railway (backend + frontend no mesmo projeto)

1. Acesse https://railway.app → New Project → Deploy from GitHub
2. O `railway.json` já está configurado no projeto
3. Adicione variável: `AION_ALLOWED_ORIGINS=*`
4. Railway fornece URL pública automaticamente

---

## Variáveis de ambiente — resumo

| Serviço | Variável | Valor |
|---------|----------|-------|
| Render (backend) | `AION_ALLOWED_ORIGINS` | URL do Vercel (ou `*` no início) |
| Render (backend) | `AION_DB_PATH` | `/tmp/aion.db` |
| Vercel (frontend) | `VITE_API_URL` | URL do Render |

---

## Observação sobre SQLite no Render

O Render usa sistema de arquivos efêmero — o banco SQLite em `/tmp/aion.db` é resetado a cada redeploy. Para dados permanentes, migre para PostgreSQL (Render oferece gratuitamente). O código backend precisa apenas trocar `sqlite3` por `psycopg2` e adaptar as queries, mas para demonstração e MVP o SQLite funciona perfeitamente.

