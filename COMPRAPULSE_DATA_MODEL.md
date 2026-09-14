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