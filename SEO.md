# SEO e indexação

- Domínio canônico único: `https://aion-news-os.vercel.app`.
- Rotas públicas em inglês: `/articles`, `/article/:slug`, `/categories`, `/tags`, `/about`, `/privacy`, `/terms` e `/contact`.
- Artigos diretos são renderizados pelo backend com canonical, hreflang `en-US`, Open Graph, Twitter Card, `NewsArticle`, `BreadcrumbList`, publisher e `ImageObject` próprios.
- A home declara `WebSite`, `NewsMediaOrganization` e `SearchAction` apontando para `/articles?q=`.
- `robots.txt`, `sitemap.xml`, `news-sitemap.xml`, `image-sitemap.xml` e `rss.xml` são dinâmicos e expostos no domínio canônico por rewrite da Vercel.
- Nenhum conteúdo publica sem texto em inglês e imagem raster HTTP/HTTPS validada, convertida para WebP 1200×630 e persistida no Render.
- A verificação técnica não garante indexação: envio no Search Console, rastreamento, aprovação no Google News e métricas de campo dependem do Google e do tempo de produção.
