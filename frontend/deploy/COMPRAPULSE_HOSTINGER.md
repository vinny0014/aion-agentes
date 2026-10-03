# CompraPulse — pacote Hostinger (pré-publicação)

Este arquivo documenta o artefato preparado; não autoriza deploy, DNS ou ativação comercial.

## Gerar

```bash
npm ci
npm run build:comprapulse
npm run package:comprapulse
```

O conteúdo de `dist/` é o pacote estático. O build inclui `.htaccess` com fallback SPA,
cabeçalhos de segurança e `noindex, nofollow`. O empacotamento rejeita source maps,
arquivos de ambiente, chaves, padrões comuns de segredo e links simbólicos; depois gera:

- `release/comprapulse-hostinger.zip`, pronto para extração na raiz confirmada;
- `release/comprapulse-hostinger.sha256`, para conferir a integridade antes do upload.

O ZIP usa ordem, permissões e timestamps determinísticos: o mesmo `dist/` produz o mesmo checksum.
Arquivos públicos editoriais do AION News (`ads.txt`, verificação Google, manifesto e service worker)
ficam fora do build e do ZIP standalone.

## Pré-condições antes de qualquer upload

- confirmar o diretório raiz destinado ao subdomínio na Hostinger, sem criar ou alterar DNS nesta etapa;
- confirmar que o workspace Render é o workspace registrado pelo usuário;
- adicionar `https://comprapulse.aionnews.cloud` a `CORS_ORIGINS` somente no deploy autorizado;
- manter `COMPRAPULSE_ENABLED=false` enquanto não houver piloto fresco e totalmente evidenciado;
- não retirar `noindex` antes de validar produção, destino, imagem, preço, estoque e tracking;
- não alterar AION News, AION Crypto, DNS ou plano contratado durante esta preparação.

Antes do upload autorizado, executar `sha256sum -c release/comprapulse-hostinger.sha256`
no diretório `frontend/`. Extrair o ZIP somente na raiz Hostinger previamente confirmada.

## Gate de publicação

O pacote pode ser enviado apenas quando existir oferta Shopee real e fresca, imagem correspondente,
destino exato, estoque confirmado e tracking comprovado. Parâmetros na URL ou dados do feed, isoladamente,
não comprovam atribuição.
