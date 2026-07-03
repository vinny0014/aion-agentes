# DEPLOY.md — resumo (detalhes: GUIA_PUBLICACAO.md e CHECKLIST_DEPLOY.md)
1. GitHub: push da branch main (CI roda 29 testes + build)
2. Render: Blueprint lê render.yaml (disco SQLite + SECRET_KEY gerada)
3. Vercel: root `frontend`, VITE_API_URL = URL do Render
4. Render: CORS_ORIGINS = URL da Vercel
Variáveis opcionais: ANTHROPIC_API_KEY/OPENAI/OPENROUTER/GEMINI (IA), VITE_GA_MEASUREMENT_ID, VITE_ADSENSE_CLIENT, VITE_CF_ANALYTICS_TOKEN, orcamento_diario_usd (settings).
