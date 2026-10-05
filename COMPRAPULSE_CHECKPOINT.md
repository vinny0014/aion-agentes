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

### Correção do gate de dependências

- CI102 / run `37071609479` falhou antes dos testes porque `pip-audit` passou a apontar 13 vulnerabilidades publicadas em `PyJWT 2.13.0`; frontend e deployment-config permaneceram verdes.
- O pin foi atualizado para `PyJWT 2.15.1`, patch mais recente da linha corrigida publicada pelo projeto oficial. Nenhuma exceção ou supressão foi adicionada ao auditor.
- Validação local após a atualização: `pip-audit` sem achados, `pip check` PASS, 85 testes backend PASS e build frontend PASS.
- Código entregue nos commits remotos `5e503b13f7e5ca66b111a5c7b1fbdd67ac3aa805` (recibo) e `4bea0279de892e16d0fcfd3893dc4638dd765cec` (PyJWT corrigido).
- CI103 / run `37071878197` COMPLETED/SUCCESS: dependências, backend, frontend, deployment-config e E2E, incluindo as 7 jornadas Playwright.

### Verificação final do recibo

- O checkpoint foi entregue em `372edc3f8cbf83270c8e02ada18e2a9cc02689e5`.
- CI104 / run `37072109423` COMPLETED/SUCCESS no mesmo head: backend, frontend, deployment-config e as 7 jornadas E2E.

## Retomada 2026-10-02 — seleção explícita do piloto no CSV

- Base remota confirmada em `372edc3f8cbf83270c8e02ada18e2a9cc02689e5`; PR #22 continua draft/open/mergeable, sem avanço concorrente observado. CI104 estava verde nessa base.
- O export oficial de 2026-09-29 permanece disponível apenas como amostra de parser, mas já excedeu a janela de frescor de 24 horas. Nenhuma oferta foi criada a partir dele.
- Adicionado fluxo opt-in por arquivo configurado no servidor: o admin escolhe explicitamente uma linha entre 0 e 499, recebe somente título, categoria, preço e timestamps sanitizados, e não recebe imagem nem URL comercial no preview.
- O servidor relê a mesma linha no momento da confirmação e exige o recibo HMAC correspondente ao conteúdo exato. Alteração do arquivo, troca de linha, recibo inválido/expirado ou registro fora da janela fresca são rejeitados antes da persistência.
- A única mutação permitida por esse fluxo é salvar o item selecionado como rascunho; publicação continua bloqueada pelos guardrails de imagem, destino, preço e tracking.
- Cobertura adicionada para seleção limitada, arquivo ausente, export expirado, alteração após preview e jornada UI de preview → rascunho. Validação local: 88 testes backend PASS, build/type-check frontend PASS e `git diff --check` PASS.
- A sessão Shopee foi revalidada novamente na rota oficial de ofertas e continua bloqueada pelo CAPTCHA deslizante. O desafio não foi tocado nem contornado; autenticação atual, preço ao vivo, destino e tracking não foram confirmados.
- Estado comercial: 0 ofertas publicadas; nenhuma atribuição, pedido ou comissão alegados; R$0 de custo recorrente novo; main, DNS e produção preservados. NOT READY.

### HUMAN ACTION REQUIRED

WHAT: concluir manualmente o CAPTCHA deslizante exibido pela Shopee.
WHERE: navegador seguro desta conversa, na rota de Ofertas Shopee Afiliados.
WHY: obter um export novo e revalidar sessão, produto, preço, imagem, destino e tracking sem presumir autenticação.
EXACT NEXT STEP: arrastar a peça do desafio uma única vez, aguardar a página de ofertas e gerar um novo export oficial; não enviar senha, código ou segredo no chat.

NEXT: aguardar CI deste bloco; após um export fresco, selecionar um único piloto pelo novo fluxo e manter somente em rascunho até imagem correspondente, destino correto e tracking atribuído serem comprovados.

### Verificação final da seleção CSV

- Código entregue no PR #22 em `a6e1f4f9d6cc2550fdc8759c249a4c64cda253ea`.
- CI105 / run `37078829145` COMPLETED/SUCCESS: dependências, 88 testes backend, build/type-check frontend, deployment-config e E2E, incluindo a nova jornada de seleção CSV → rascunho.
- Branch local e remota reconciliadas; nenhuma oferta foi persistida ou publicada por esta execução.
- NEXT: ação humana no CAPTCHA e novo export oficial fresco; depois validar um único piloto sem liberar publicação antes das evidências de imagem, destino, preço e tracking.

## Retomada 2026-10-02 — evidência técnica fail-closed

- Base remota confirmada em `152bc4dd29cbcf81a45e7427c0ac8a14c0e4a999`; árvore limpa/sincronizada, PR #22 aberto e CI106 / run `37079050532` COMPLETED/SUCCESS antes das alterações.
- Adicionado verificador técnico opt-in para um único rascunho fresco. Ele segue no máximo cinco redirecionamentos HTTPS, aceita somente hosts Shopee/Shopee CDN, rejeita DNS privado/reservado, limita imagem a 8 MB e exige raster JPEG/PNG/WebP/AVIF decodificável com pelo menos 200×200.
- O destino só passa quando termina no `shop_id:item_id` exato do registro oficial. Redirecionamento inseguro, loop, produto divergente, resposta inesperada, imagem falsa ou pequena falha fechado.
- A evidência persistida é apenas um hash `cp-tech-v1`; URLs, corpo de resposta e conteúdo da imagem não entram no relatório admin nem no log.
- Mesmo quando destino e imagem passam, o status permanece `REVIEW_REQUIRED`, com `stock_valid=false`, `tracking_verified=false` e `publishable=false`. O endpoint não pode aprovar nem publicar oferta.
- O recurso é desativado por padrão (`COMPRAPULSE_TECHNICAL_VERIFY_ENABLED=false`) e exige administrador e ativação explícita. O painel informa separadamente que estoque/tracking continuam pendentes.
- Cobertura adicionada para destino correto, raster real, produto divergente, redirecionamento privado, imagem falsa, recurso desativado e impossibilidade de publicação. Validação local: 91 testes backend PASS, build/type-check frontend PASS e `git diff --check` PASS.
- Nenhum request real à Shopee foi disparado neste bloco, porque não existe rascunho fresco e a sessão continua atrás do mesmo CAPTCHA já registrado. Nenhuma oferta foi persistida/publicada; DNS, Render, main e produção preservados. NOT READY.

NEXT: aguardar CI do verificador; após export oficial fresco, salvar um único rascunho, ativar o verificador técnico no ambiente autorizado e observar o destino real. Tracking, estoque e publicação continuam bloqueados até evidência oficial independente.

### Verificação final da evidência técnica

- Código entregue no PR #22 em `21e3c84edb23af0c4238347b91b782ff5c1e08c2`.
- CI107 / run `37081900125` COMPLETED/SUCCESS: dependências, 91 testes backend, build/type-check frontend, deployment-config e E2E, incluindo a jornada de evidência técnica com publicação bloqueada.
- Branch local/remota reconciliadas; nenhum ambiente externo foi alterado e nenhuma oferta foi publicada.

## Retomada 2026-10-03 — vitrine premium sem dados fictícios

- Base remota confirmada em `53214aad2e588ed9a47678b4afe390f4ac60c0c0`; árvore limpa/sincronizada, PR #22 aberto e CI108 / run `37082082235` COMPLETED/SUCCESS antes das alterações.
- A home CompraPulse foi alinhada ao mockup aprovado com identidade própria: header escuro, hero, busca central, filtro de categoria, prova visual do gate, vitrine responsiva, cards premium e disclosure de afiliado preservado.
- Contagem, categorias, imagem, título, preço, data e destino são derivados exclusivamente das ofertas ativas retornadas pelo catálogo. Desconto, avaliação, quantidade vendida, cupom e ranking não aparecem porque ainda não há evidência desses campos.
- Catálogo vazio permanece explicitamente vazio, inclusive em 360/390/430/1440 px; nenhum produto, imagem, preço ou CTA fictício foi criado para preencher o layout.
- Adicionado contrato E2E para uma resposta interceptada: a vitrine exibe somente o registro validado fornecido, preserva o href Shopee exato e remove o card quando a busca não corresponde.
- Validação local: 91 testes backend PASS, build/type-check frontend PASS e `git diff --check` PASS. O E2E local não iniciou o Chromium ausente neste ambiente; a suíte será executada pelo CI do commit.
- Nenhuma oferta real foi persistida/publicada e nenhum ambiente externo, DNS, Render, main ou produção foi alterado. NOT READY.

### Correção do gate npm da vitrine

- A vitrine foi entregue em `ffc3604c88f23f8f827de970e2013b72583f675c`. O CI109 / run `37093289301` interrompeu a execução no gate de dependências por novos avisos do `npm audit`: `braces` transitivo via Tailwind 3.4.19 e React Router 6.30.6. Backend e deployment-config passaram; o E2E não foi executado porque o gate falhou antes dele.
- React Router foi atualizado para 7.18.4 e Tailwind/PostCSS para 4.3.3. A configuração PostCSS e as composições CSS foram migradas para a sintaxe suportada, sem suprimir nem ignorar o auditor.
- Validação local após a correção: `npm audit --audit-level=high` sem vulnerabilidades, build/type-check frontend PASS, 91 testes backend PASS e `git diff --check` PASS.
- Esta correção altera somente dependências e CSS do frontend; nenhuma oferta, integração, ambiente externo, DNS ou produção foi alterado.

### Verificação final da vitrine e do gate npm

- Correção entregue no PR #22 em `18fcc1b6d90e583ec532741a1055f011b3817d29`.
- CI110 / run `37093694578` COMPLETED/SUCCESS: gate de dependências, 91 testes backend, build/type-check e smoke test frontend, deployment-config e 9 jornadas Playwright, incluindo a vitrine com catálogo interceptado.
- O CI comprova o contrato técnico com dados de teste controlados; não comprova oferta, preço, estoque, destino ou tracking real da Shopee. Publicação continua bloqueada até todas essas evidências reais existirem.

NEXT: após export fresco e piloto totalmente evidenciado, os mesmos cards receberão apenas os produtos reais que passarem todos os gates.

## Retomada 2026-10-03 — build standalone preparado

- Base remota confirmada em `43b4eefb81ac7ddb0b2ea331f52a5d9dd4632b82`; árvore inicialmente limpa/sincronizada, PR #22 draft/open/mergeable e CI111 / run `37093829888` COMPLETED/SUCCESS.
- A sessão Shopee foi revalidada na rota oficial e continua exibindo o mesmo CAPTCHA deslizante. O desafio não foi tocado; autenticação atual, oferta fresca e tracking continuam não comprovados.
- Adicionado build `npm run build:comprapulse`, separado do shell AION News: raiz própria, rotas `/produto/:id`, `/admin` e `/login`, links internos adaptáveis e telemetria/service worker editorial desativados nesse modo.
- O artefato standalone usa metadados `pt-BR`, ícone próprio, canonical futuro `https://comprapulse.aionnews.cloud/` e permanece `noindex, nofollow` até publicação e validação reais. Nenhum DNS foi alterado.
- O frontend standalone aponta explicitamente para o backend Render existente e requer, no deploy autorizado, incluir a origem final em `CORS_ORIGINS`; nenhuma variável ou serviço externo foi alterado neste bloco.
- O CI passa a construir e testar os dois artefatos e a repetir as jornadas CompraPulse no modo standalone. Isso valida separação de rotas sem liberar ofertas nem afrouxar os gates comerciais.
- Validação local: builds AION News e CompraPulse PASS, smoke HTTP standalone PASS, `npm audit --audit-level=high` sem vulnerabilidades, 91 testes backend PASS e `git diff --check` PASS. Playwright standalone aguarda o CI porque o Chromium local continua ausente.
- Estado comercial inalterado: 0 ofertas publicadas; nenhuma atribuição, pedido ou comissão alegados; R$0 de custo recorrente novo; main, DNS, Render e produção preservados. NOT READY.

### Correção do contrato de deployment

- O CI112 / run `37096920689` confirmou frontend e smoke standalone PASS, mas bloqueou o E2E porque um teste de configuração ainda exigia literalmente a expressão antiga de API same-origin.
- O teste foi atualizado para comprovar as duas regras: AION News continua same-origin em produção e somente o build standalone explicitamente marcado usa o endpoint Render configurado. Também valida as duas variáveis do modo CompraPulse; nenhum gate foi removido ou ignorado.

### Verificação final do build standalone

- Build standalone entregue em `4a01bba582c21760c6dd2b89d7d9d8d9af2dc143`; correção do contrato de teste entregue em `e85238658eb0db31bd0034529193d974ab517598`.
- CI113 / run `37097041535` COMPLETED/SUCCESS: dependências e 91 testes backend, configuração de deploy, builds e smoke tests AION News/CompraPulse, 9 jornadas Playwright legadas e as mesmas 9 jornadas novamente no modo standalone.
- O artefato está tecnicamente preparado para hospedagem separada, mas continua deliberadamente não publicado e `noindex`; CORS, DNS e ambiente Render só podem ser alterados no workspace confirmado e após as evidências comerciais reais.

NEXT: somente com export fresco, validar um piloto real e manter `noindex` e publicação bloqueada até imagem, preço, destino, estoque e tracking estarem comprovados.

## Retomada 2026-10-03 — pacote Hostinger seguro

- Base remota confirmada em `8d45c959d46a6fa2b298715233d4502449754a3a`; árvore inicialmente limpa/sincronizada, PR #22 draft/open/mergeable e CI114 / run `37097191632` COMPLETED/SUCCESS.
- A rota oficial Shopee foi revalidada e continua no mesmo CAPTCHA deslizante. Nenhuma interação com o desafio ocorreu; sessão, oferta fresca e tracking permanecem não comprovados.
- O build standalone agora inclui `.htaccess` somente no modo CompraPulse, com fallback SPA para `/produto/:id`, cabeçalhos de segurança, CSP limitada ao backend Render existente, `index.html` sem cache e `X-Robots-Tag: noindex, nofollow`.
- O build normal do AION News não recebe esse arquivo, preservando a separação e a configuração editorial existente.
- Adicionado runbook de pré-publicação Hostinger com condições fail-closed: workspace Render confirmado, CORS apenas no deploy autorizado, módulo desabilitado sem piloto fresco e proibição de retirar `noindex` antes das evidências reais.
- O CI valida a presença e os controles essenciais do pacote, sem fazer upload, alterar DNS ou modificar ambiente externo.
- Validação local: builds AION News/CompraPulse PASS, `.htaccess` exclusivo do standalone PASS, `npm audit --audit-level=high` sem vulnerabilidades, 91 testes backend PASS e `git diff --check` PASS.
- Estado comercial inalterado: nenhuma oferta publicada e nenhum tracking, pedido ou comissão alegados. R$0 de custo recorrente novo; main, DNS, Hostinger, Render e produção preservados. NOT READY.

### Verificação final do pacote Hostinger

- Pacote entregue no PR #22 em `583eb395eaa03439d1c18259bcaf580b295cc2de`.
- CI115 / run `37098867984` COMPLETED/SUCCESS: dependências e 91 testes backend, configuração de deploy, builds e smoke tests AION News/CompraPulse, pacote `.htaccess` standalone e jornadas Playwright nos modos integrado e standalone.
- O resultado comprova somente o artefato de hospedagem: nenhum upload, DNS, CORS, workspace Render, Hostinger ou ambiente de produção foi alterado.
- Estado comercial permanece fail-closed: nenhuma oferta publicada e nenhum preço fresco, estoque, destino atribuído ou tracking real alegado.

NEXT: somente um export oficial fresco e evidências reais permitem validar um piloto; upload e deploy controlado continuam bloqueados até imagem, preço, destino, estoque e tracking estarem comprovados.

## Retomada 2026-10-03 — artefato Hostinger isolado e reproduzível

- Base remota confirmada em `b12e2a4b6bb65583628fc638a020b3b45b6aeae7`; árvore inicialmente limpa/sincronizada, PR #22 draft/open/mergeable e CI116 / run `37113277510` COMPLETED/SUCCESS.
- A rota oficial Shopee foi revalidada, mas carregou uma superfície vazia sem lista de ofertas nem evidência de sessão autenticada. Nenhum CAPTCHA, login ou outro controle foi tocado; oferta fresca e tracking continuam não comprovados.
- A inspeção do primeiro ZIP revelou resíduos editoriais do build anterior (`ads.txt`, verificação Google, manifesto e service worker). O empacotamento falhou fechado e esses arquivos não foram aceitos.
- O modo standalone agora usa entrada React própria, login/404 próprios e `publicDir` isolado. O pacote não carrega rotas/chunks editoriais nem arquivos públicos do AION News.
- Adicionado empacotador determinístico baseado no manifesto Vite. Ele aceita apenas `index.html`, `.htaccess`, ícone e assets declarados; rejeita caminhos inesperados, links simbólicos, source maps, chaves, arquivos de ambiente e padrões comuns de segredo.
- `npm run package:comprapulse` gera `release/comprapulse-hostinger.zip` e checksum SHA-256 verificável. Duas execuções locais sobre o mesmo build produziram o mesmo hash; o ZIP final contém somente nove arquivos standalone.
- Validação local: `npm audit --audit-level=high` sem vulnerabilidades, builds AION News/CompraPulse PASS, pacote/checksum/ZIP PASS, 91 testes backend PASS e `git diff --check` PASS. O Playwright local iniciou backend/preview, mas não executou por ausência do Chromium transitório; a suíte completa permanece obrigatória no CI.
- Nenhum ZIP foi enviado, nenhum DNS/CORS/Render/Hostinger/produção foi alterado e nenhuma oferta foi publicada. NOT READY.

NEXT: aguardar CI do isolamento e empacotamento; publicação continua bloqueada até export fresco e evidências reais de imagem, preço, destino, estoque e tracking.

### Correção do contrato visual standalone

- O CI117 / run `37120970389` aprovou backend, deployment-config, build, isolamento do ZIP e 10 jornadas integradas, mas uma das nove jornadas standalone falhou porque a fixture ainda apontava para `og-cover.png`, corretamente removido junto com os assets editoriais.
- A jornada agora serve sua própria imagem SVG controlada e continua exigindo card, título, preço e destino exatos. Nenhuma asserção ou gate foi removido; o teste não depende mais de um asset do AION News.

NEXT: aguardar novo CI completo; somente depois registrar o artefato Hostinger como tecnicamente pronto para upload controlado.

### Verificação final do artefato isolado

- Isolamento e empacotador entregues em `409df47a828b62f170754dcbc4dcfdf8d67054c2`; fixture standalone corrigida em `2c1793d049e75562b35ed51a2b3f012d07644745`.
- CI118 / run `37121133513` COMPLETED/SUCCESS: dependências e 91 testes backend, deployment-config, builds/smoke tests, ZIP/checksum Hostinger, 10 jornadas Playwright integradas e nove jornadas CompraPulse standalone.
- O ZIP é tecnicamente reproduzível e isolado, mas não foi enviado. `noindex`, módulo desabilitado e todos os gates comerciais permanecem ativos.

NEXT: obter export oficial fresco e comprovar imagem, preço, destino, estoque e tracking do piloto antes de qualquer upload ou publicação.

## Retomada 2026-10-03 — validação de acessos e gates

- PR #22 continua aberto, draft e mergeável na branch `codex/comprapulse-mvp`. Antes deste registro, o código estava no head `d8213ce44e8a3ebb51f732f275ada842be646a7e`; CI #119 / run `37121291044` terminou COMPLETED/SUCCESS.
- CI #119 aprovou os quatro jobs: `deployment-config`, `backend`, `frontend` e `e2e`. O frontend fez build/type-check e smoke test do CompraPulse standalone; E2E executou as jornadas de navegador.
- Hostinger: a navegação para hPanel no navegador em nuvem mostrou página em branco. As instruções fornecidas pelo próprio site informam que o login é bloqueado nesse navegador e proíbem nova tentativa de autenticação/takeover. Portanto, subdomínio, sessão e diretório de publicação não puderam ser inspecionados. Nenhum upload ou DNS foi alterado.
- Render: workspace confirmado como `My Workspace` (`tea-d8opf7gg4nts7397q24g`). A lista contém `aion-news-api` (branch `codex/aion-news-render-manus-bridge`, plano Starter) e `aion-agentes-api` (branch `main`, plano Free), sem serviço dedicado CompraPulse.
- O build standalone ainda configura `https://aion-news-api.onrender.com` como origem de API. A branch seguida por esse serviço não contém `backend/app/commerce/router.py` (HTTP 404 no GitHub); `main` também não contém esse módulo. Assim, a origem configurada não está servindo o backend CompraPulse do PR. Não alteramos branch de serviço, CORS, variáveis ou deploy para preservar AION News e serviços existentes.
- Shopee: `https://affiliate.shopee.com.br/dashboard` abriu com o título do painel, mas a árvore acessível e a captura ficaram em branco. Nenhuma oferta, estado de sessão autorizada ou tracking pôde ser confirmado. O desafio registrado anteriormente na rota de ofertas não foi tocado nem contornado. O export conhecido de 2026-09-29 está vencido pela regra de 24 horas.
- Gate comercial permanece FAIL-CLOSED: zero ofertas atuais validadas; imagem, preço, disponibilidade, destino e atribuição afiliada não foram comprovados. Nenhum produto/link foi publicado. `COMPRAPULSE_ENABLED=false` e `noindex,nofollow` devem permanecer até evidências frescas e completas.
- Nenhum deploy ou upload foi feito; não houve mudança em `main`, AION News, DNS, Hostinger ou Render, nem custo fixo novo.

### HUMAN ACTION REQUIRED

- **O QUE:** gerar um novo export oficial de ofertas Shopee (CSV ou formato oficial disponível), com dados atualizados.
- **ONDE:** painel Shopee Afiliados autenticado, área de ofertas/feed de produtos.
- **POR QUÊ:** a página do painel não renderizou ofertas nesta verificação e o último export conhecido tem mais de 24 horas; sem fonte fresca não é possível validar produto, preço, estoque, destino e tracking.
- **JÁ PRONTO:** adapter oficial CSV, preview sem publicação, recibo obrigatório, verificador técnico fail-closed, build standalone Hostinger isolado e CI #119 verde.
- **PRÓXIMO PASSO EXATO:** disponibilizar aqui o novo export oficial; validar um piloto e só liberar qualquer publicação se destino, imagem, disponibilidade e tracking passarem. Não compartilhar senha, código ou segredo.

### Estado desta retomada

**NOT READY.** O artefato está tecnicamente validado, mas a autenticação/feed Shopee, o backend Render isolado e o acesso à pasta Hostinger continuam sem confirmação; nenhuma produção foi alterada.

### Checagem Shopee atual — CAPTCHA falhou

- Na tentativa de retomar pelo Work em 2026-10-03, o painel oficial redirecionou para `/verify/captcha`. A tela exibiu “Tente Novamente Mais Tarde” e “A verificação falhou. Tente novamente em alguns minutos.”
- A tela bloqueia o acesso ao dashboard, ofertas e export; não foi possível confirmar a sessão autenticada nem obter produto, preço, disponibilidade, imagem, destino ou tracking atual.
- Nenhuma interação foi feita com o botão “Tentar Novamente”; o CAPTCHA não foi resolvido ou contornado. A condição foi registrada como bloqueio de CAPTCHA.
- Estado NOT READY permanece. O export conhecido de 2026-09-29 continua fora da janela de 24 horas; não publicar produtos ou links com base nele.

#### HUMAN ACTION REQUIRED — atualização

- **O QUE:** aguardar alguns minutos e concluir manualmente a verificação oficial da Shopee, caso o painel a solicite; depois gerar um export oficial novo das ofertas.
- **ONDE:** sessão oficial Shopee Afiliados, área de ofertas/feed.
- **POR QUÊ:** a Shopee informa falha na verificação e bloqueia ofertas atuais; é necessária evidência fresca para validar o piloto e o tracking.
- **JÁ PRONTO:** CI #120 verde, build/package standalone isolado, adapter/preview e guardrails fail-closed.
- **PRÓXIMO PASSO EXATO:** após concluir a verificação, baixar um export oficial atualizado e disponibilizá-lo aqui. Não enviar senha, OTP, cookies ou tokens.

## Retomada 2026-10-05 — checagem de publicação

- PR #22 continua aberto em draft, na branch codex/comprapulse-mvp; main permanece intacta.
- CI #121 / run 37165491421 terminou com sucesso nos quatro jobs: backend, deployment-config, frontend e E2E. Isso valida os testes do branch, não uma oferta real nem um deploy.
- O conector do Opera respondeu que o navegador não está conectado. Não foi possível ler as abas autenticadas da Hostinger ou Shopee nesta sessão. A última observação registrada da Shopee (2026-10-03) foi falha na verificação; o último export conhecido, de 2026-09-29, está vencido pela regra de 24 horas.
- O workspace Render My Workspace foi confirmado. Serviços existentes: aion-crypto-api, aion-news-api e aion-agentes-api; não há serviço dedicado CompraPulse nem instância Postgres no workspace.
- O pacote frontend standalone ainda usa VITE_API_URL=https://aion-news-api.onrender.com. Esse serviço acompanha a branch codex/aion-news-render-manus-bridge; a rota backend/app/commerce/router.py não existe nessa branch. Não alterar a branch, CORS ou variáveis do AION News para contornar isso.
- O branch CompraPulse contém o router /api/commerce, mas backend/app/main.py também inicia o scheduler editorial e o orquestrador do AION News. Falta um entrypoint/deploy backend isolado para CompraPulse.
- O backend atual usa SQLite. Não há banco persistente no workspace. Um serviço Render Free perde arquivos locais ao reiniciar ou sair do idle e não é apropriado para armazenar o catálogo comercial em produção; documentação: https://render.com/docs/free.
- Hostinger ainda sem diretório de publicação confirmado; nenhum ZIP enviado, DNS ou serviço alterado. A URL pública não foi validada. Não publicar enquanto os gates permanecerem pendentes.

### Estado após a checagem

**NOT READY.** Falta uma sessão Opera conectada, um export Shopee oficial e fresco com destino/estoque/tracking comprovados, e um backend CompraPulse isolado com persistência adequada. Nenhum produto foi publicado; nenhum serviço pago, custo ou alteração em AION News/main foi criado.

### Ação humana necessária

- **O QUE:** conectar o Opera Browser Connector ao Work, ativando “Allow AI connection” no Opera e entrando na conta Opera se solicitado.
- **ONDE:** ícone/extensão Browser Connector no Opera, com as abas Hostinger e Shopee já abertas.
- **POR QUÊ:** a ferramenta informa “Browser not connected” e não pode observar a sessão autorizada nem concluir as validações comerciais e de publicação.
- **JÁ PRONTO:** branch/PR preservados, CI #121 verde, pacote standalone Hostinger, guardrails fail-closed e auditoria do workspace Render concluídos.
- **PRÓXIMO PASSO EXATO:** após conectar, dizer “conectado”; verificar as abas e, se a Shopee solicitar desafio humano, concluí-lo no site oficial e exportar ofertas atualizadas. Não enviar senha, códigos, cookies ou tokens.