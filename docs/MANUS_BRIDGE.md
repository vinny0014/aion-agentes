# Ponte operacional Work ↔ Manus — AION News

Esta integração separa responsabilidades sem usar Vinicio como mensageiro:

- o Work/Codex altera código, testa, usa branches e PRs;
- o Manus opera navegador, Render, Hostinger, GA4 e Search Console;
- o backend recebe eventos de tarefas do Manus e mantém auditoria idempotente;
- comentários `@codex` no PR de coordenação iniciam o trabalho do Codex no contexto correto;
- pagamento, CAPTCHA e 2FA continuam como bloqueios humanos.

## Endpoints

| Método | Caminho | Finalidade | Proteção |
|---|---|---|---|
| `GET` | `/internal/manus/status` | Confirma somente capacidades configuradas | Público, sem valores |
| `POST` | `/internal/manus/webhook` | Recebe `task_created` e `task_stopped` | RSA-SHA256 após ativação |
| `GET` | `/internal/manus/events` | Lista a fila de eventos | `X-Aion-Bridge-Token` |
| `POST` | `/internal/manus/events/{event_id}/ack` | Marca evento processado | `X-Aion-Bridge-Token` |
| `POST` | `/internal/manus/tasks` | Cria tarefa privada no Manus | `X-Aion-Bridge-Token` |
| `POST` | `/internal/manus/tasks/{task_id}/messages` | Continua uma tarefa | `X-Aion-Bridge-Token` |

O endpoint público aceita no máximo 64 KiB. Sem chave pública ele responde ao teste de cadastro, mas não interpreta nem persiste o corpo. Com a chave configurada, exige os cabeçalhos `X-Webhook-Signature` e `X-Webhook-Timestamp`, valida RSA-SHA256, rejeita entregas com mais de cinco minutos e deduplica por `event_id`.

O middleware limita o webhook a 120 solicitações por minuto por origem. Toda tarefa ou continuação enviada pela ponte recebe automaticamente as travas contra pagamento, DNS, exclusão destrutiva e exposição de segredos.

## Variáveis do Render

- `MANUS_API_KEY`: chave da API v2 criada exclusivamente para o AION News.
- `MANUS_WEBHOOK_PUBLIC_KEY`: PEM retornado por `webhook.publicKey`.
- `MANUS_PROJECT_ID`: ID da pasta/projeto AION NEWS no Manus.
- `AION_BRIDGE_TOKEN`: token aleatório exclusivo, com no mínimo 32 caracteres.

Nunca use chaves do AION Crypto. Nunca exponha valores em chat, GitHub, relatório ou log.

## Ativação

1. Implantar a branch aprovada no Render e confirmar `/api/health`.
2. Criar uma chave de API v2 exclusiva no Manus.
3. Consultar a chave pública do webhook e salvá-la no Render.
4. Salvar também `MANUS_API_KEY`, `MANUS_PROJECT_ID` e um novo `AION_BRIDGE_TOKEN`.
5. Confirmar que `/internal/manus/status` mostra três valores `true`.
6. Cadastrar `https://aion-news-api.onrender.com/internal/manus/webhook` no Manus.
7. Criar uma tarefa privada de teste na pasta AION NEWS.
8. Confirmar a chegada dos eventos `task_created` e `task_stopped` sem duplicidade.
9. Usar o PR de coordenação para handoffs de código: o Manus publica um comentário começando por `@codex`, acompanha o CI e valida o deploy após o retorno do Codex.

## Limites de autonomia

A ponte não confirma pagamentos, compras, exclusões, DNS, envio de e-mail ou outras ações irreversíveis. O endpoint oferece criação de tarefas e mensagens, mas não implementa `task.confirmAction`. Quando o Manus parar com `stop_reason=ask`, o Work pode responder somente se a escolha for técnica, segura e reversível. Pagamento, CAPTCHA e 2FA são encaminhados a Vinicio.
