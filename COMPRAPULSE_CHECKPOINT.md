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
