# CompraPulse — estado atual

## Escopo confirmado

- Reutilizar integralmente `aionnews.cloud` e a infraestrutura atual.
- Custo fixo novo: **R$ 0,00**.
- Fase 1: **somente Shopee Brasil**.
- Não implementar Amazon ou Mercado Livre nesta fase.
- Preservar o AION News atual em `main`; toda migração começa nesta branch dedicada.

## Infraestrutura encontrada

- Repositório: `vinny0014/aion-agentes`.
- Branch de produção/base: `main`.
- Frontend atual: React 18 + Vite + TypeScript + React Router.
- Backend atual: FastAPI + APScheduler + pytest + httpx.
- Estrutura existente inclui frontend, backend, painel admin, telemetria, CI e documentação operacional.
- Último commit visível em `main` antes desta migração: `c6e4e9a45990edf325217b76db9f934373e2b671`.

## Estado da migração CompraPulse

Nesta baseline ainda não havia código CompraPulse no repositório nem branch específica. Portanto esta branch é o primeiro ponto seguro de implementação sem alterar produção.

## Princípios de segurança

1. Nenhum produto entra em produção sem dados reais da Shopee.
2. Nenhuma URL é tratada como afiliada apenas por heurística.
3. O link de afiliado oficial deve ser armazenado exatamente como recebido da fonte autorizada.
4. Imagens devem ser reais e corresponder ao produto/oferta.
5. Se link, produto ou imagem não passarem validação, a oferta fica indisponível para tráfego.
6. Nenhum secret será salvo no GitHub.

## Próximo bloco técnico

1. Criar modelo de dados de comércio e atribuição.
2. Criar `AffiliateLinkGuardian` e kill-switch de oferta.
3. Criar estrutura de jobs idempotentes para descoberta/revalidação.
4. Criar páginas CompraPulse em paralelo ao frontend legado.
5. Só publicar produtos após integração autorizada ou importação oficial da Shopee.
