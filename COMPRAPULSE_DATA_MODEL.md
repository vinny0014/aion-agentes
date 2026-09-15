# CompraPulse — modelo de dados MVP Shopee

## products
- id
- external_product_id
- title
- slug
- brand
- category_id
- description
- primary_image_url
- status (`draft`, `active`, `paused`, `removed`)
- created_at
- updated_at

## offers
- id
- product_id
- marketplace (`shopee`)
- seller_name
- price
- original_price
- discount_percent
- rating
- review_count
- sold_count
- stock_state
- source_url
- affiliate_link_id
- last_checked_at
- status

## affiliate_links
- id
- product_id
- offer_id
- affiliate_url_exact
- source
- status (`VALID`, `INVALID`, `EXPIRED`, `MISMATCH`, `UNKNOWN`, `REVIEW_REQUIRED`)
- technically_valid
- expected_product_id
- destination_product_id
- last_http_status
- last_checked_at
- created_at

Regra: `affiliate_url_exact` é imutável por padrão. Substituição exige nova versão/registro e nova validação.

## product_images
- id
- product_id
- image_url
- source
- status
- last_checked_at

## price_history
- id
- product_id
- offer_id
- price
- original_price
- observed_at
- source

## events
- id
- event_id
- anonymous_session_id
- event_type
- product_id
- offer_id
- affiliate_link_id
- price_at_event
- utm_source
- utm_medium
- utm_campaign
- utm_content
- placement
- occurred_at

Eventos mínimos:
- `landing_view`
- `category_view`
- `product_view`
- `shopee_click`
- `affiliate_redirect_success`
- `affiliate_redirect_error`

## orders
- id
- marketplace_order_id
- product_id
- offer_id
- order_value
- status
- ordered_at
- imported_at

## commissions
- id
- order_id
- amount
- status (`pending`, `approved`, `rejected`)
- approved_at
- imported_at

## jobs
- id
- job_type
- entity_id
- input_hash
- status
- attempt
- started_at
- finished_at
- error_code

Jobs MVP:
- `discover_products`
- `refresh_offer`
- `validate_affiliate_link`
- `validate_image`
- `calculate_pulse_score`
- `publish_offer`
- `unpublish_offer`
- `import_commissions`
- `reconcile_attribution`

## Regra de publicação / kill switch

Uma oferta só pode receber tráfego quando, ao mesmo tempo:

- produto = `active`;
- oferta = `active`;
- imagem = válida;
- link afiliado = `VALID`;
- destino corresponde ao produto esperado;
- preço é válido e recente.

Falha em qualquer item deve marcar a oferta como `paused` antes de novo tráfego.

## Implementação persistente — 2026-09-14

As entidades implementadas usam prefixo `cp_` para não colidir com AION News.
`store.py` usa o SQLite existente. `COMPRAPULSE_ENABLED=false` é o padrão:
nenhuma tabela commerce é criada em produção até habilitação explícita.

Importação atual: JSON normalizado com exatamente os campos:
`product_id`, `title`, `category`, `price_cents`, `observed_at`, `expires_at`,
`affiliate_url`, `source_url`, `image_url`, `image_source`, `source`.
Datas: Unix UTC em segundos; moeda BRL em centavos inteiros; fonte:
`shopee_official_export` ou `shopee_official_api`. Observação não pode estar no
futuro ou ter mais de 24h; validade máxima de 24h desde a observação.
Esses rótulos não comprovam procedência: todo import entra em DRAFT.

Validação de rede/proveniência NÃO é implementada pelo import. Somente um
adapter oficial testado poderá gravar evidência via `record_check`, sem endpoint
HTTP de autoaprovação. A evidência inclui correspondência de produto/variação,
tracking, imagem decodificada e estoque, com prazo máximo de 1h. `record_score`
recebe componentes com evidência; dados faltantes nunca aumentam o score.
`publish` exige score elegível >=70 e validação completa. Leitura do catálogo
reconfere validade e pausa ofertas inválidas mesmo que o cron não execute.

Jobs: chave tipo/entidade/hash/ciclo, transação de claim, lease 120s, até três
execuções com backoff, acknowledgement cercado por token. Sem adapter oficial,
`discover_products`/`refresh_offer` ficam BLOCKED. O scheduler horário está
configurado, mas desligado por padrão; não existe operação 24h comprovada.

Eventos públicos: landing_view, category_view, product_view, merchant_click,
com consentimento explícito e event_id UUID. Valores de preço são obtidos no
servidor. Pedidos e comissões não podem ser criados pelo endpoint de eventos.
Ledger de comissão/custos tem tabelas, mas importação/reconciliação ainda faltam;
a UI mostra não conectado e não apresenta zero como lucro comercial apurado.

Rotas de preparação: /comprapulse, /comprapulse/produto/:id,
/comprapulse/admin. A Home e /admin legados permanecem. Antes do corte para /
e /produto/:slug: backup real, adapter, QA browser, metadata SSR da Hostinger,
URLs estáveis por produto (não por snapshot), conexão do backend e deploy.

Amostra oficial CSV/XLSX e documentação autenticada ainda são necessárias para
mapear campos reais, não inferir preço/estoque/variação/comissão. Sem isso não
implementar suposições como se fossem uma integração validada.
