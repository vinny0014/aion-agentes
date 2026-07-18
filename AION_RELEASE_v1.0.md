# AION AI NEWS OS — release de produção

## Arquitetura

Monorepo existente com SPA React 18, Vite 8, TypeScript e Tailwind; API FastAPI em Python 3.12; SQLite em disco persistente; autenticação JWT Bearer com refresh rotativo; e scheduler APScheduler. O registro contém 35 agentes e o orquestrador executa um pipeline de 30 etapas.

## Superfícies públicas

As rotas públicas são exclusivamente em inglês: Home, Articles, Article, Categories, Tags, About, Privacy, Terms e Contact. Artigos diretos são renderizados no backend para entregar canonical, Open Graph, Twitter Card, `NewsArticle`, `BreadcrumbList`, publisher e `ImageObject` antes do JavaScript.

O domínio canônico único é `https://aion-news-os.vercel.app`; o backend oficial é `https://aion-news-api.onrender.com`. A Vercel encaminha API, HTML de artigos, imagens, `robots.txt`, três sitemaps e RSS ao Render.

## Publicação e imagens

Com um provedor configurado, a fila produz rascunhos completos; sem provedor, produz rascunhos offline estruturados e registra a pendência. Nada publica automaticamente sem aprovação do Fact Check, texto público em inglês e imagem raster real.

Imagens remotas e uploads passam por validação de formato, dimensão, tamanho e destino de rede, são normalizados para WebP 1200×630 e persistidos no disco Render. SVG, data URI, imagem vazia, placeholder ou URL não materializada mantêm o conteúdo em draft. A imagem validada alimenta thumbnail, hero, Open Graph, Twitter e image sitemap.

## SEO e Google

O projeto fornece canonical, hreflang `en-US`/`x-default`, Open Graph, Twitter Cards, `WebSite`, `NewsMediaOrganization`, `SearchAction`, `NewsArticle`, `BreadcrumbList`, publisher e `ImageObject`. `robots.txt`, sitemap geral, news sitemap de 48 horas, image sitemap e RSS 2.0 são dinâmicos e usam somente o domínio oficial.

Isso estabelece prontidão técnica, sem prometer rastreamento, indexação, Google News, Discover ou Core Web Vitals de campo, que dependem dos serviços externos e do conteúdo publicado.

## Segurança e entrega

Senhas usam bcrypt; refresh tokens são rotativos e revogáveis; CORS aceita somente a origem oficial em produção; endpoints editoriais críticos exigem administrador; há rate limits, CSP, HSTS e demais headers de segurança. Segredos ficam em variáveis protegidas e `render.yaml` gera `SECRET_KEY` e `ADMIN_SETUP_TOKEN`.

O GitHub Actions executa compilação e testes do backend, auditoria de dependências Python, instalação reproduzível, auditoria npm, type-check/build Vite, smoke do preview e validação das configurações de deploy. O Render só implanta depois que os checks vinculados passam.
