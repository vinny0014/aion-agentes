# Guia de publicação oficial

O projeto existente deve ser publicado sem recriar estrutura ou histórico.

## GitHub

- Repositório: `https://github.com/vinny0014/aion-agentes`
- Branch de produção: `main`
- Antes do deploy, confirme que os jobs `backend` e `frontend` do GitHub Actions estão verdes.

## Render

1. Aplique o Blueprint do `render.yaml` sobre o repositório oficial.
2. Confirme o serviço `aion-news-api` e a URL `https://aion-news-api.onrender.com`.
3. Não copie valores de `SECRET_KEY` ou `ADMIN_SETUP_TOKEN` para arquivos. O Render os gera como variáveis protegidas.
4. Confirme o disco em `/var/data` e `GET https://aion-news-api.onrender.com/api/health` com status `ok`.

## Vercel

1. Importe o mesmo repositório, selecionando `frontend` como Root Directory.
2. Use Vite, `npm run build` e output `dist`.
3. Mantenha `VITE_API_URL` vazio: `frontend/vercel.json` usa rewrites para o backend oficial e preserva uma única origem pública.
4. Confirme o domínio `https://aionnews.cloud` e o deploy automático da `main`.

## Primeiro acesso editorial

1. Consulte o valor de `ADMIN_SETUP_TOKEN` no painel seguro do Render.
2. Abra `/signup`, preencha o token somente na criação da primeira conta administrativa e depois faça login.
3. No Editorial Studio, envie PNG/JPEG/WebP/GIF com no mínimo 600×315 ou gere uma capa real.
4. A publicação será recusada se o conteúdo não estiver em inglês ou se a imagem não puder ser validada e persistida.

## Smoke test de produção

```bash
curl -I https://aionnews.cloud/
curl https://aionnews.cloud/api/health
curl https://aionnews.cloud/robots.txt
curl https://aionnews.cloud/sitemap.xml
curl https://aionnews.cloud/news-sitemap.xml
curl https://aionnews.cloud/image-sitemap.xml
curl https://aionnews.cloud/rss.xml
```

Valide também `/articles`, busca, categorias, tags, newsletter, 404, login, dashboard, upload, publicação, edição, destaque, breaking e agendamento.
