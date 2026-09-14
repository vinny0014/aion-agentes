# CompraPulse — checkpoint de retomada

DATE/TIME: 2026-09-14 UTC
BRANCH: codex/comprapulse-mvp
LAST COMMIT: 276a56b6446e9f0895f543c9f5b1dcffa91d5c4f (base deste bloco)
PR: https://github.com/vinny0014/aion-agentes/pull/22 (draft)

COMPLETED: baseline, modelo de dados documental, guardrails e quatro testes recuperados.
CURRENT STATE: implementação retomada no PR existente; main e produção intocados.
TEST STATUS: CI 34799174354 backend/config PASS; frontend FAIL em npm audit
(browserslist vulnerável); E2E não executou. Não é erro dos testes commerce.
KNOWN ISSUES: sem persistência commerce, catálogo operacional ou integração Shopee.
NEXT TASK: persistência transacional, fila idempotente, expiração, testes; corrigir audit.
HUMAN BLOCKERS: acesso autorizado Shopee ainda não verificado. Revisão automática
do navegador recusou execução por limite de uso, não por ação insegura.

## Histórico

- Retomada: PR #22 confirmou branch e SHA acima; diretório limpo. Nenhum trabalho
  anterior foi substituído. O MVP Sites separado foi recuperado somente para
  consulta; usa D1 e autenticação própria e não é portável à Hostinger sem adaptação.
- A branch real da Hostinger indicada no histórico é codex/aion-production-final;
  main é o legado Vercel. Confirmar bindings em painel antes de qualquer deploy.
- Nenhum produto real importado, nenhum anúncio contratado, automação não ativada.

## Bloco implementado — 2026-09-14T02:42:52.775150+00:00

DATE/TIME: 2026-09-14T02:42:52.775161+00:00
BRANCH: codex/comprapulse-mvp
LAST COMMIT: base 276a56b; alterações deste bloco serão incluídas no commit que
contém este checkpoint (consultar git log -1 -- COMPRAPULSE_CHECKPOINT.md).
PR: #22, draft; não mesclar main.
COMPLETED:
- Protocolo permanente em AGENTS.md e checkpoint com histórico.
- SQLite cp_* transacional: snapshots imutáveis de ofertas, links exatos,
  histórico de preço, evidências, scores, eventos, ledger e jobs.
- Gates de publicação exigem imagem/estoque/proveniência/tracking, produto
  correto, validade e PulseScore elegível >=70. Expiração é aplicada na leitura.
- Fila idempotente, claim exclusivo, lease com fencing, retries e backoff.
- API com admin existente, importação apenas DRAFT, catálogo e eventos separados
  de comissões/pedidos. Nenhuma rota permite marcar link VALID manualmente.
- /comprapulse, /comprapulse/produto/:id e /comprapulse/admin implementados,
  sem imagens/produtos fictícios. Botão usa URL afiliada exata; sendBeacon opt-in.
- Rotas de preparação noindex por header Vercel; Home legada preservada.
- Removido bloqueio npm audit HIGH atualizando dependências compatíveis.
CURRENT STATE: módulo opt-in COMPRAPULSE_ENABLED=false. Código preparado, não
implantado na Hostinger/Render. Dados reais: zero. Operação 24h não comprovada.
TEST STATUS: 65 testes backend PASS (31 commerce); build/typecheck PASS;
npm audit --audit-level=high PASS (dois alertas moderados restantes);
git diff --check PASS. QA visual e E2E real Shopee NÃO executados.
KNOWN ISSUES:
- React Router: dois alertas moderados, correção exige avaliar migração 7.x.
- Adapter oficial, validação HTTP/redirecionamentos/imagem/proveniência ainda
  não conectados; jobs faltantes retornam BLOCKED, nunca DONE fictício.
- CSV/XLSX real, relatório de comissões, atribuição e aprendizado de lucro pendentes.
- Sem limite de publicação por hora implementado; manter publicação automática desativada.
- Antes de produção: SSR/canonical Hostinger e URLs estáveis por produto,
  QA visual/mobile/E2E, backup SQLite real e confirmação de branch de deploy.
NEXT TASK: recuperar documentação/amostra oficial Shopee com acesso autorizado;
implementar adapter e testes de contrato; conferir CI do novo SHA no PR #22.
HUMAN BLOCKERS: navegador indisponível por falha de revisão automática decorrente
do limite de uso; sessão/autorização Shopee não verificada. Não pedir senhas.
O portal fornecido retornou apenas shell JavaScript na busca pública; isso não
prova acesso autenticado nem indisponibilidade da Shopee.

Não usar o MVP Sites como se já estivesse migrado; não alterar main ou produção
até concluir backup e validação. Custo fixo novo contratado: R$ 0,00.

## Checkpoint de entrega — 2026-09-14T02:46:27.173963+00:00

DATE/TIME: 2026-09-14T02:46:27.173974+00:00
BRANCH: codex/comprapulse-mvp
LAST COMMIT: 40aff2a8dedc4048382b5db2150ef4632d1398f6 (código validado)
PR: #22 (draft, atualizado e persistido no GitHub)
COMPLETED: bloco técnico acima salvo; árvore remota idêntica à árvore local
validada: 070d5144c71e933e15c8de02cdab19c818f9ad80.
CURRENT STATE: retomada aguardando autenticação Shopee; produção preservada.
TEST STATUS: CI 34800200903 / run 83 — backend PASS, frontend PASS,
deployment-config PASS, E2E legado PASS. 65 testes locais PASS.
KNOWN ISSUES: E2E Shopee real e QA visual CompraPulse ainda pendentes;
as demais lacunas do bloco anterior continuam válidas.
NEXT TASK: autenticação segura no painel afiliado; inspecionar documentação
oficial e permissões API/export antes de implementar o adapter real.
HUMAN BLOCKERS: login Shopee confirmado: portal /offer/product_offer
redirecionou para /buyer/login. A falha temporária do navegador foi resolvida
na retomada. Não é mais bloqueio de uso. Entrada segura será solicitada;
se não concluída, manter imports em DRAFT e jobs sem adapter BLOCKED.

Não confundir CI verde/preview Vercel com migração concluída: Hostinger/Render
não receberam este módulo, nenhuma oferta real foi publicada e o cron não foi
habilitado. Retomar daqui, sem recriar a baseline ou substituir main.

## Retomada automática — 2026-09-14T07:36:00Z

DATE/TIME: 2026-09-14T07:36:00Z
BRANCH: codex/comprapulse-mvp
LAST COMMIT: 684e1a40f7fa1076709e57dcc437a78e11380309
PR: #22 (draft)
COMPLETED:
- Implementado orçamento transacional de publicação automática: no máximo 10
  jobs publish_offer por hora UTC, compartilhado por retries/workers concorrentes.
- Reexecuções no mesmo ciclo não conseguem enfileirar um segundo lote acima do teto.
- publish_offer agora é executado localmente pelo worker e continua fail-closed:
  o store revalida evidência oficial, produto exato, imagem, estoque, tracking,
  validade e PulseScore antes de ativar a oferta.
- Adicionado teste com 12 ofertas de fixture provando teto de 10, idempotência e
  que somente as 10 enfileiradas podem ficar ativas.
CURRENT STATE: produção/main continuam intocados; nenhuma oferta real publicada.
TEST STATUS: CI run 85 (34818442514) PASS — backend, frontend,
deployment-config e E2E legado todos verdes.
KNOWN ISSUES: integração oficial Shopee/autenticação ainda é o bloqueio principal;
QA visual CompraPulse e E2E real com oferta Shopee permanecem pendentes.
NEXT TASK: com acesso autorizado, implementar adapter oficial e testes de contrato
para validar destino, imagem real, estoque/proveniência e tracking antes de publicar.
HUMAN BLOCKERS: sessão autenticada/API/export oficial Shopee ainda não disponível
nesta execução. Não solicitar ou armazenar senha; manter jobs externos BLOCKED.

Custo fixo novo contratado: R$ 0,00. Produção não alterada.

## Retomada automática — 2026-09-14T17:24:00Z

DATE/TIME: 2026-09-14T17:24:00Z
BRANCH: codex/comprapulse-mvp
PR: #22 (draft; main/produção preservados)
COMPLETED:
- Confirmado que o head anterior bc3b6f91e4a37b7f9bae3a8db713cd86950ce543 tinha CI run 90 PASS.
- Preservado preview seguro de importação oficial já existente: lotes limitados,
  sem persistência/publicação e sem eco de URLs/segredos em resposta administrativa.
- Adicionado contrato explícito OfficialOfferAdapter para futura fonte autorizada
  Shopee, sem rede, sem credenciais e sem assumir API inexistente.
- Adicionado DisabledShopeeAdapter fail-closed: até haver acesso oficial autorizado,
  qualquer tentativa retorna official_shopee_adapter_not_configured.
- Adicionado bounded_batch com teto rígido, verificação de identidade da fonte e
  rejeição de adapters que excedam o limite solicitado.
- Adicionados testes unitários cobrindo fail-closed, limites, mismatch e lote acima
  do teto. Commits: 49809ac3351b5f01e568337818045ce0dbe6a396 e
  fb7b1d7f74ef522aef287ee644f543235e26cffb.
CURRENT STATE: nenhuma integração externa foi ativada; nenhuma oferta real foi
publicada; nenhum custo novo; secrets continuam fora do código.
TEST STATUS: o head anterior estava verde. O workflow dos dois novos commits ainda
não apareceu na consulta imediatamente após o push; verificar o CI do novo head na
próxima retomada e corrigir qualquer falha antes de avançar.
KNOWN ISSUES: sessão/API/export oficial Shopee ainda indisponível para esta execução;
E2E real, imagem real e atribuição real não podem ser validados sem fonte autorizada.
NEXT TASK: verificar CI do novo head; depois conectar uma implementação concreta do
OfficialOfferAdapter somente quando houver acesso autorizado, mantendo preview antes
de persistência e publicação.
HUMAN BLOCKERS: autenticação/permissão Shopee oficial. Não solicitar nem armazenar senha.

Custo fixo novo contratado: R$ 0,00. Produção e main não alteradas.
