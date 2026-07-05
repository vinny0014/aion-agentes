# CHANGELOG — Operação Image Agent Omega (v5.3)

## Regra absoluta atingida: nenhum artigo sem imagem
- **Image Agent** (novo): garante imagem em todo artigo — oficial do feed (com image_alt, image_credit, image_width, image_height, source_url) ou **arte editorial SVG determinística 1200×630** gerada localmente (custo zero, sem IA, sem rede, data-URI que nunca quebra).
- **Image Repair Agent** (novo): varre o acervo, completa qualquer image_url vazio, idempotente, sem duplicar. No pipeline.
- **Publisher** chama o Image Agent ao publicar → Radar e artigos saem já com imagem.
- **Bootstrap** cria os guias iniciais já com arte editorial.
- **Fact Check** bloqueia auto-publicação de artigo IA sem imagem (além de categoria/resumo/500 palavras).
- **Banco**: colunas image_alt, image_credit, image_width, image_height (migração automática).
- **Frontend**: hero, cards de últimas notícias, miniaturas da sidebar "Hoje em IA", imagem principal do artigo e cards "Leia também" consomem image_url real com alt correto, width/height (anti-CLS), loading=lazy e fetchPriority no hero. Placeholder roxo só aparece se, teoricamente, image_url fosse vazio — o que não ocorre mais.
- **SEO**: novo **/image-sitemap.xml** (Google Discover/News); JSON-LD já inclui image.

## Pipeline: 29 etapas (Discovery→Research→Trend→Breaking→Content→FactCheck→SEO→**Image**→ImagePrompt→**ImageRepair**→ImageOpt→Publisher→…)

## Arquivos modificados
backend: core/database.py · agents/imagegen.py (novo) · agents/team.py · agents/registry.py · agents/orchestrator.py · routers/public.py · main.py · bootstrap.py · tests/test_api.py
frontend: src/pages/Landing.tsx · src/pages/Blog.tsx

## Testes: 55/55 (7 novos de imagem). Evidência: home renderiza arte editorial, 0 imagens quebradas.
