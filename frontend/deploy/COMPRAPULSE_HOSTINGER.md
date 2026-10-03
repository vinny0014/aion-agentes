# CompraPulse — pacote Hostinger (pré-publicação)

Este arquivo documenta o artefato preparado; não autoriza deploy, DNS ou ativação comercial.

## Gerar

```bash
npm ci
npm run build:comprapulse
```

O conteúdo de `dist/` é o pacote estático. O build inclui `.htaccess` com fallback SPA,
cabeçalhos de segurança e `noindex, nofollow`.

## Pré-condições antes de qualquer upload

- confirmar o diretório raiz destinado ao subdomínio na Hostinger, sem criar ou alterar DNS nesta etapa;
- confirmar que o workspace Render é o workspace registrado pelo usuário;
- adicionar `https://comprapulse.aionnews.cloud` a `CORS_ORIGINS` somente no deploy autorizado;
- manter `COMPRAPULSE_ENABLED=false` enquanto não houver piloto fresco e totalmente evidenciado;
- não retirar `noindex` antes de validar produção, destino, imagem, preço, estoque e tracking;
- não alterar AION News, AION Crypto, DNS ou plano contratado durante esta preparação.

## Gate de publicação

O pacote pode ser enviado apenas quando existir oferta Shopee real e fresca, imagem correspondente,
destino exato, estoque confirmado e tracking comprovado. Parâmetros na URL ou dados do feed, isoladamente,
não comprovam atribuição.
