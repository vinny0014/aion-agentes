# Checklist de deploy — AION AI NEWS OS

- [ ] GitHub Actions verde na `main`.
- [ ] Render Blueprint aplicado com o serviço `aion-news-api` saudável em `/api/health`.
- [ ] Disco Render `/var/data` montado e persistindo banco e uploads.
- [ ] Vercel com Root Directory `frontend`, deploy automático e domínio `https://aion-news-os.vercel.app`.
- [ ] `/api/health`, `/robots.txt`, os três sitemaps e `/rss.xml` respondendo pelo domínio da Vercel.
- [ ] Primeiro administrador criado com o `ADMIN_SETUP_TOKEN` do Render; token guardado fora do Git.
- [ ] Fluxo editorial validado: upload/geração de imagem raster → salvar → publicar → artigo visível em `/articles`.
- [ ] Artigo direto apresenta canonical, Open Graph, Twitter Card e `NewsArticle` próprios.
- [ ] Search Console: propriedade verificada e os três sitemaps enviados (etapa humana).
- [ ] Google News/Discover e Core Web Vitals acompanhados após tráfego real (etapa externa).
