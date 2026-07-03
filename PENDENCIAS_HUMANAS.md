# PENDÊNCIAS HUMANAS — AION AGENTES

Tudo abaixo depende exclusivamente de credenciais/autorização sua. O restante do sistema está pronto e operando.

## 1. Publicar no GitHub
- **Etapa parada:** push do repositório (exige login/token GitHub).
- **O que fazer:** crie um repositório em github.com/new e execute:
  ```bash
  cd aion-agentes
  git remote add origin https://github.com/SEU_USUARIO/aion-agentes.git
  git push -u origin main
  ```

## 2. Deploy do frontend (Vercel)
- **Etapa parada:** login OAuth na Vercel.
- **O que fazer:** vercel.com → Add New → Project → importe o repositório →
  Root Directory: `frontend` → adicione a variável `VITE_API_URL` com a URL do backend no Render → Deploy.
- O `vercel.json` já está configurado (build, output e rewrite de SPA).

## 3. Deploy do backend (Render)
- **Etapa parada:** login/autorização no Render.
- **O que fazer:** render.com → New → Blueprint → aponte para o repositório.
  O `render.yaml` cria o serviço, o disco do SQLite e gera o `SECRET_KEY`.
  Ajuste `CORS_ORIGINS` para o domínio final do frontend.

## 4. Ativar geração de conteúdo por IA
- **Etapa parada:** falta ao menos uma API key (OpenAI, Anthropic, OpenRouter ou Gemini) — envolve conta e pagamento.
- **O que fazer:** obtenha a chave no provedor escolhido e adicione ao `.env` do backend
  (localmente) ou às Environment Variables do Render (produção). Itens da fila marcados
  como `blocked` voltam a processar no próximo ciclo do scheduler ou via
  `POST /api/pipeline/run`.

## 5. Domínio próprio (opcional)
- **O que fazer:** compre/aponte o domínio na Vercel e atualize as URLs canônicas em
  `frontend/index.html`, `public/robots.txt`, `public/sitemap.xml` e `backend/app/main.py`.
