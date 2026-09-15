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
