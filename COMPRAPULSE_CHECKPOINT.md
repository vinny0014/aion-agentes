# CompraPulse — checkpoint de retomada

DATE/TIME: 2026-09-15T03:22:00Z
BRANCH: codex/comprapulse-mvp
PR: #22 (draft; mergeable; main/produção preservados)

## Estado consolidado

COMPLETED:
- Baseline/migração segura preservados; módulo CompraPulse permanece opt-in e sem deploy em produção.
- Persistência SQLite cp_* transacional, snapshots/histórico, eventos, ledger e fila idempotente com lease/retry/backoff.
- Guardrails fail-closed: publicação exige evidência oficial, produto correto, imagem/estoque/tracking válidos, validade e PulseScore >= 70.
- Orçamento transacional limita publicação automática a no máximo 10 jobs publish_offer por hora UTC, inclusive com retries/workers concorrentes.
- Frontend /comprapulse, produto e admin preparados sem produtos/imagens fictícios.
- Preview de importação oficial limitado a 500 registros, sem persistência/publicação e sem eco de URLs/segredos.
- Contrato OfficialOfferAdapter e DisabledShopeeAdapter fail-closed implementados; nenhuma rede/credencial presumida.
- preview_adapter_records aceita somente shopee_official_export ou shopee_official_api e rejeita lote com proveniência divergente/misturada.
- CI do head e72d41f664b4f9dfa29ba4685df9653a21a28b93: run 96 (34904254766) COMPLETED/SUCCESS.

CURRENT STATE:
- PR #22 aberto, draft e mergeable.
- Nenhuma integração externa Shopee ativada.
- Nenhuma oferta real publicada.
- Nenhum custo fixo novo.
- Secrets continuam fora do código.
- main e produção permanecem intactas.

TEST STATUS:
- CI run 96 verde no head e72d41f664b4f9dfa29ba4685df9653a21a28b93.
- E2E real Shopee, imagem real, destino real e atribuição real continuam impossíveis de validar sem fonte autorizada.

KNOWN ISSUES:
- Falta sessão/API/export oficial Shopee autorizado para implementar adapter concreto.
- QA visual/mobile CompraPulse e E2E com oferta real permanecem pendentes.
- Antes de produção ainda confirmar branch/bindings Hostinger/Render, backup real e estratégia SSR/canonical/URLs estáveis.

NEXT TASK:
- Quando houver fonte oficial autorizada, implementar adapter concreto a partir da amostra/documentação real, mantendo preview antes de qualquer persistência/publicação.
- Validar destino do link, imagem real, estoque/proveniência e tracking; somente então liberar ingestão/persistência progressiva.
- Não inventar schema de export/API nem transformar URL comum em link afiliado.

HUMAN BLOCKERS:
- Autenticação/permissão Shopee oficial ou export oficial autorizado. Não solicitar, registrar ou armazenar senha.

Custo fixo novo contratado: R$ 0,00. Produção e main não alteradas.

## Histórico resumido

2026-09-14: baseline, store transacional, jobs, guardrails, frontend opt-in e CI inicial estabilizados.
2026-09-14T07:36Z: teto transacional de 10 publicações/hora implementado e testado.
2026-09-14T17:24Z: OfficialOfferAdapter/DisabledShopeeAdapter e limites de lote implementados.
2026-09-14T22:28Z: adapter conectado ao preview; somente origens oficiais reconhecidas e proveniência uniforme aceitas.
2026-09-15T03:22Z: confirmado CI run 96 SUCCESS no head e72d41f; integração real permanece corretamente bloqueada até fonte Shopee autorizada.

## Retomada 2026-09-28 — auditoria e preview do painel

- Base remota confirmada e6c18099; PR22 draft/open/mergeable; CI97 SUCCESS.
- Auditoria atual detalhada em COMPRAPULSE_AUDIT_2026-09-28.md, com DONE/PARTIAL/MISSING por módulo.
- Admin agora chama preview, mostra dados fornecidos, exige confirmação separada para rascunho e invalida preview em edição.
- Copy comercial sem promessa de melhor preço não comprovada.
- 41 testes commerce PASS; build/type-check PASS; testes UI novos adicionados, aguardando CI (Chromium local com download inválido).
- Fonte Shopee aberta no navegador redireciona para login. Zero ofertas reais lidas/importadas/publicadas; tracking não verificado.
- NEXT: autenticação segura Shopee; implementar adapter a partir da estrutura observada; completar gaps da auditoria; QA e E2E antes de produção.
- main/produção preservadas, custo novo R$0. NOT READY.

### Verificação final deste bloco

- Código entregue: c628801ef2f4f8d7c1af1ba53b38acfdff115d85 no PR22.
- CI98 / run36457630998 SUCCESS: backend, frontend, deployment-config e e2e. Os testes UI novos passaram no CI; isso não comprova integração real Shopee.
- Solicitação segura de login interrompida; autenticação não confirmada. Nenhuma nova tentativa automática de login.
- Próxima ação humana continua sendo autenticar a sessão Shopee; adapter real, piloto e tracking pendentes.

## Retomada 2026-09-29 — feed oficial e adapter CSV

- Base remota confirmada no head `ccdcd6c85aaa652ba3a5ecf6f26158f98aad21fa`; PR #22 draft/open e sem execução concorrente observada.
- CI99 / run `36460940223` confirmado SUCCESS no mesmo head: backend, frontend, deployment-config e e2e; Playwright registrou 7 testes aprovados.
- Sessão Shopee Afiliados autenticada confirmada na conta do usuário. A rota Oferta Shopee carregou, mas estava sem dados naquele filtro.
- A rota Feed de produto exigiu CAPTCHA. Nenhuma tentativa automática de resolver o desafio foi feita.
- CSV oficial autenticado já baixado foi localizado: UTF-8 com BOM, 199.061.991 bytes e cabeçalho real com `itemid`, preço, título, categorias, imagem, `product_link` e `product_short link`.
- Implementado `ShopeeOfficialCsvAdapter`: leitura em fluxo, limite de lote, schema mínimo real, preço decimal em centavos, identidade `shop_id:item_id`, imagem HTTPS e correspondência exata entre `origin_link` e `product_link`.
- O adapter preserva o link do export, mas não declara atribuição/tracking. Não houve persistência nem publicação.
- Validação real side-effect-free: 100 registros iniciais do CSV aceitos, 0 rejeitados, `persisted=false`, `published=false`.
- Testes locais: 83 backend PASS; `git diff --check` PASS.
- NEXT: conectar o adapter a um comando/admin de preview por arquivo com recibo e seleção explícita de piloto; persistir somente rascunho escolhido; depois validar destino HTTP, imagem decodificada, estoque e tracking antes de qualquer publicação.
- HUMAN BLOCKER: CAPTCHA apenas para nova navegação/download do Feed de produto. O CSV existente permite continuar o parser e o preview sem contornar o desafio.
- Estado comercial: 0 ofertas persistidas/publicadas nesta retomada; tracking, clique atribuído, pedido e comissão continuam não comprovados. R$0 de custo recorrente novo. NOT READY.

### Verificação final do adapter CSV

- Código entregue no PR #22: `952bae9eb3b8b16d8eedfa487bdb05c4e02961cf`.
- CI100 / run `36608719818` COMPLETED/SUCCESS no commit entregue.
- Branch remota e cópia local reconciliadas; árvore remota idêntica ao bloco testado.

## Retomada 2026-10-02 — recibo obrigatório entre preview e rascunho

- Base remota confirmada no head `57a75dc5bbcdf5aa1db18c1c6421085b31e6d8a5`; PR #22 continua draft/open/mergeable e sem avanço concorrente observado.
- CI101 / run `36609033636` confirmado COMPLETED/SUCCESS no mesmo head.
- A ingestão admin direta agora exige um recibo HMAC de curta duração emitido somente para um registro aceito pelo preview. O recibo expira em 5 minutos, é vinculado ao conteúdo normalizado exato e não contém URLs ou campos comerciais.
- Registro ausente, alterado, expirado ou com assinatura inválida é rejeitado antes da persistência. A UI conserva o recibo apenas no estado do preview e o envia junto ao registro confirmado.
- Testes novos cobrem vínculo exato, expiração, adulteração, rejeição do formato legado e o fluxo API preview → rascunho. Testes locais: 85 backend PASS; build frontend PASS; `git diff --check` PASS.
- E2E local iniciou backend/frontend, mas não executou por ausência do binário Chromium neste ambiente. O teste atualizado será executado pelo CI do commit; isso não é evidência de E2E real Shopee.
- Sessão Shopee revalidada em 2026-10-02: a rota oficial de ofertas redireciona imediatamente para um CAPTCHA deslizante (`Verifique para continuar`). O desafio não foi tocado nem contornado; portanto autenticação, ofertas ao vivo e tracking não puderam ser reconfirmados.
- Estado comercial permanece fail-closed: 0 ofertas publicadas; nenhuma atribuição, pedido ou comissão alegados; R$0 de custo recorrente novo; main/produção preservadas. NOT READY.

### HUMAN ACTION REQUIRED

WHAT: concluir manualmente o CAPTCHA deslizante exibido pela Shopee.
WHERE: navegador seguro desta conversa, na rota de Ofertas Shopee Afiliados.
WHY: o CAPTCHA bloqueia a confirmação da sessão atual e qualquer validação ao vivo de produto, destino e tracking.
WHAT IS ALREADY COMPLETE: adapter do CSV oficial, preview sem efeitos colaterais, recibo obrigatório antes do rascunho, testes backend e build frontend.
EXACT NEXT STEP: arrastar a peça do desafio uma única vez e aguardar o redirecionamento para a página de ofertas; não enviar senha, código ou segredo no chat. Depois, revalidar sessão e selecionar um piloto real sem publicar até destino, imagem, preço e tracking passarem.

NEXT: aguardar CI do recibo; então ligar seleção explícita de um item do CSV ao fluxo de preview/rascunho e implementar evidência técnica de imagem/destino, mantendo publicação bloqueada até tracking comprovado.
