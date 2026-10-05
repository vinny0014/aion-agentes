# CompraPulse — auditoria de produção, 28/09/2026

Base auditada: PR #22, branch codex/comprapulse-mvp, e6c18099d8d7ecf4c0d2f2a59f36042defe11bea.
GitHub confirmado: aberto, draft, mergeable. CI run 97 (34924773366) success no head anterior.

| Área | Estado | Evidência / pendência |
|---|---|---|
| Pacote Commerce | DONE | backend/app/commerce isolado, feature flag opt-in |
| Modelos/persistência | PARTIAL | cp_products, cp_offers, cp_link_checks, cp_scores, cp_price_history, cp_jobs, cp_events, cp_commissions, cp_costs, cp_audit. Campos seller, descrição, rating, sold_count, desconto e ImportJob dedicado ausentes |
| Migrations | PARTIAL | inicialização idempotente, transações, FKs, UNIQUE e índice cp_jobs_due; falta migração versionada com rollback e plano de backup testado |
| Services/guardrails | PARTIAL | publicação exige evidência recente, produto, estoque, imagem, tracking e score. Verificação externa não conectada |
| Adapter Shopee | MISSING | contrato OfficialOfferAdapter e DisabledShopeeAdapter; nenhum parser real autorizado |
| Jobs | PARTIAL | fila idempotente, lease/retry/backoff e scheduler opt-in; handlers de rede não conectados |
| API | PARTIAL | catálogo, eventos, admin, preview e ingestão de rascunho; faltam operações administrativas completas |
| Frontend | PARTIAL | catálogo, produto, categorias presentes, busca por título; faltam seller, seções/rankings, relacionados e SEO de produção |
| Admin/preview | PARTIAL | painel agora exige preview e confirmação separada; edição invalida preview. API direta de ingestão continua sendo admin-only e valida novamente, mas não exige recibo de preview |
| Analytics | PARTIAL | consentimento, contagens internas e ledger; faltam janelas 1d/7d, CTR e rankings; nenhuma conversão atribuída comprovada |
| Tests | PARTIAL | 41 testes comerciais passam; build/type-check passam. Novos testes UI usam API interceptada, não são E2E real Shopee |
| Deploy/piloto | MISSING | nenhum deploy nesta execução, nenhuma oferta importada ou publicada; DNS/bindings/backup ainda não verificados |

## Alterações deste bloco

- Preview visual no admin antes de salvar rascunho: título, imagem indicada, preço, categoria e URLs exatas fornecidas pelo operador. Não inventa seller/desconto ausentes.
- Preview não salva dados; salvar exige ação separada. Edição do JSON invalida o preview. Entrada fica bloqueada durante solicitações para evitar salvar outra versão do conteúdo.
- Formato aceito não é aprovação de imagem/destino/tracking. Rejeição impede salvar pelo painel.
- Removida promessa não comprovada de melhor preço e maior volume de vendas.
- Seis testes UI adicionados: preview/edição/salvamento, rejeição e quatro larguras. Fixtures só em teste interceptado, sem persistência real.

## Shopee / afiliação / piloto

Tentativa real de navegação em https://affiliate.shopee.com.br/offer/shopee_offer redirecionou para login da Shopee. Não há sessão autenticada disponível nesta execução. Sem evidência de CAPTCHA ou bloqueio por bot.
Ofertas reais testadas/importadas/publicadas: 0. Links com tracking comprovado: 0. Rejeições reais e divergências de destino: não avaliadas. Cliques atribuídos e vendas: não verificados.
Não é possível mapear a estrutura autenticada sem autenticação. Não criar parser ou tracking por suposição.

## Validação

- 41 testes pytest commerce: PASS.
- npm run build (tsc + Vite): PASS.
- git diff --check: PASS.
- Chromium local: tentativa de instalação retornou arquivo inválido/truncado; testes UI novos dependem de execução no CI.
- QA visual, performance e E2E real: PENDING.

## HUMAN ACTION REQUIRED

WHAT: autenticar a conta Shopee Afiliados.
WHERE: sessão segura do navegador desta conversa, na tela de login Shopee já aberta.
WHY: a página oficial exige login e nenhum dado real pode ser presumido.
WHAT IS ALREADY COMPLETE: auditoria, preview no painel, ajuste de copy, 41 testes comerciais e build local.
EXACT NEXT STEP: concluir autenticação pelo fluxo seguro; depois inspecionar ofertas autorizadas e mapear o adapter concreto. Nunca enviar senha ou código no chat.

## Custos / veredito

Novo custo recorrente contratado: R$ 0,00.
NOT READY — SPECIFIC BLOCKERS REMAIN.
Login é o próximo bloqueio humano; ainda existe trabalho técnico pendente depois dele. Nenhuma alegação de operação 24h, tracking validado ou prontidão comercial.

## Resultado posterior do CI

Commit c628801ef2f4f8d7c1af1ba53b38acfdff115d85 entregue ao PR22. Run98 / 36457630998 SUCCESS, incluindo backend, frontend, deployment-config e e2e (Run browser journeys SUCCESS). Testes UI novos aprovados no CI. O download Chromium local falhou, mas Chromium e testes executaram no GitHub Actions. Não confundir este resultado com E2E real Shopee.
Solicitação segura de autenticação interrompida; acesso autenticado não confirmado.
