# CHANGELOG — Operação Image Agent Omega (v5.3)

## Histórico da fase Omega (substituído pelo gate atual)
- A implementação original usava arte editorial SVG/data URI. Esse comportamento foi removido: a versão de produção exige imagem raster real, validada, convertida para WebP 1200×630 e persistida em URL HTTP/HTTPS; sem imagem válida, o conteúdo permanece em draft.
- **Image Repair Agent** (novo): varre o acervo, completa qualquer image_url vazio, idempotente, sem duplicar. No pipeline.
- **Publisher** só publica depois de Image Agent, Image Quality e Fact Check aprovarem.
- **Bootstrap** cria guias iniciais como drafts bloqueados por imagem.
- **Fact Check** bloqueia auto-publicação de artigo IA sem imagem (além de categoria/resumo/500 palavras).
- **Banco**: colunas image_alt, image_credit, image_width, image_height (migração automática).
- **Frontend**: hero, cards de últimas notícias, miniaturas da sidebar "Hoje em IA", imagem principal do artigo e cards "Leia também" consomem image_url real com alt correto, width/height (anti-CLS), loading=lazy e fetchPriority no hero. Placeholder roxo só aparece se, teoricamente, image_url fosse vazio — o que não ocorre mais.
- **SEO**: novo **/image-sitemap.xml** (Google Discover/News); JSON-LD já inclui image.

## Pipeline: 29 etapas (Discovery→Research→Trend→Breaking→Content→FactCheck→SEO→**Image**→ImagePrompt→**ImageRepair**→ImageOpt→Publisher→…)

## Arquivos modificados
backend: core/database.py · agents/imagegen.py (novo) · agents/team.py · agents/registry.py · agents/orchestrator.py · routers/public.py · main.py · bootstrap.py · tests/test_api.py
frontend: src/pages/Landing.tsx · src/pages/Blog.tsx

## Estado atual
A suíte de produção cobre upload, bloqueio de SVG/data URI, persistência WebP, feeds e metadados por artigo.
