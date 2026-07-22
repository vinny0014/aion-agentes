# Pendências externas e humanas

O código pode preparar a infraestrutura, mas estas ações exigem contas ou decisões do proprietário:

- Confirmar os deploys automáticos da `main` nos painéis Vercel e Render.
- Guardar os valores gerados de `SECRET_KEY` e `ADMIN_SETUP_TOKEN` fora do Git.
- Criar o primeiro administrador usando o token de setup do Render.
- Adicionar uma chave de provedor de IA se a redação automática completa for desejada.
- Conectar `https://aionnews.cloud` ao projeto Vercel antes do merge da migração canônica.
- Verificar `https://aionnews.cloud` no Google Search Console e enviar `sitemap.xml`, `news-sitemap.xml` e `image-sitemap.xml`.
- Solicitar participação no Google News, quando editorialmente elegível.
- Acompanhar Core Web Vitals, rastreamento, indexação e Discover após existirem dados reais de campo.
- Configurar opcionalmente GA4, AdSense, Cloudflare Analytics e Clarity por variáveis protegidas da Vercel.

Nenhum desses serviços externos deve ter credenciais salvas no repositório.
