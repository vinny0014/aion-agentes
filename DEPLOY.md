# Deploy oficial

1. GitHub: `vinny0014/aion-agentes`, branch `main`; o CI executa testes do backend e build TypeScript/Vite.
2. Render: o Blueprint `render.yaml` cria `aion-news-api` em `https://aion-news-api.onrender.com`, com disco persistente em `/var/data`.
3. Vercel: conecte `https://aionnews.cloud` ao projeto existente, com Root Directory `frontend`.
4. O `frontend/vercel.json` encaminha `/api/*`, `/article/*`, robots, RSS, sitemaps, favicon e ícones ao Render. Logo e capa Open Graph ficam como PNGs raster estáticos na Vercel. `VITE_API_URL` deve ficar vazio; assim o navegador usa o domínio oficial como origem única.
5. `CORS_ORIGINS`, `SITE_URL` e `PUBLIC_API_URL` já estão fixados nos serviços oficiais pelo Blueprint.
6. Guarde fora do Git os valores gerados de `SECRET_KEY` e `ADMIN_SETUP_TOKEN`. O token de setup é necessário somente para criar o primeiro administrador.

Variáveis opcionais: chaves OpenAI/Anthropic/OpenRouter/Gemini no Render; GA4, AdSense, Cloudflare Analytics e Clarity na Vercel.
