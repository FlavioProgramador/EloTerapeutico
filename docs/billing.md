# Billing e Assinaturas

O módulo de Billing gerencia planos, assinaturas e pagamentos da assinatura do terapeuta no Elo Terapêutico. Ele não processa pagamentos de pacientes e não envia dados clínicos ao gateway.

## Visão geral

Fluxo do checkout Asaas:

1. A landing page pública renderiza a seção **Planos** com dados vindos de `GET /api/v1/billing/plans/`.
2. O usuário escolhe Essencial, Profissional ou Premium.
3. Se não estiver logado, o frontend redireciona para cadastro/login preservando o plano em `plan` e o destino em `next`.
4. Se estiver logado, o frontend abre `/checkout?plan=<slug>`.
5. O checkout em etapas coleta apenas dados não sensíveis: valor do plano, descrição, tipo, parcelamento quando cobrança única, vencimento e `billingType`.
6. O backend cria `customer` e `subscription` no Asaas Sandbox.
7. A assinatura local é criada como `PENDING`.
8. O Asaas envia `webhook`.
9. O backend valida o webhook e atualiza a assinatura para `ACTIVE` somente após `PAYMENT_CONFIRMED` ou `PAYMENT_RECEIVED`.
10. O sistema libera os módulos conforme o plano.

Regra central: **nada no frontend ativa plano**.

## Variáveis de ambiente

```env
ASAAS_API_KEY=
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
ASAAS_WEBHOOK_TOKEN=
BILLING_TRIAL_DAYS=7
BILLING_DEFAULT_CURRENCY=BRL
```

Regras:

- Nunca versionar chave real do Asaas.
- Em desenvolvimento, usar `https://api-sandbox.asaas.com/v3`.
- Em produção, `ASAAS_BASE_URL` não pode conter `sandbox`.
- `ASAAS_WEBHOOK_TOKEN` deve ser configurado em produção.
- Não armazenar cartão, CVV ou dados sensíveis.
- `CREDIT_CARD` só deve ser habilitado via checkout/tokenização segura futura.

## Webhook Asaas

Endpoint:

```http
POST /api/v1/billing/webhooks/asaas/
```

Alias compatível:

```http
POST /api/billing/webhooks/asaas/
```

Envie o token configurado em um destes headers:

- `asaas-access-token`
- `x-asaas-token`
- `x-webhook-token`
- `Authorization: Bearer <token>`

Eventos processados:

- `PAYMENT_CREATED`
- `PAYMENT_CONFIRMED`
- `PAYMENT_RECEIVED`
- `PAYMENT_OVERDUE`
- `PAYMENT_DELETED`
- `PAYMENT_REFUNDED`
- `SUBSCRIPTION_CREATED`
- `SUBSCRIPTION_UPDATED`
- `SUBSCRIPTION_DELETED`

O webhook é idempotente por `payload_hash` e usa `event_id` quando disponível. Eventos duplicados retornam `200` sem reprocessar.

## Endpoints

```http
GET  /api/v1/billing/plans/
POST /api/v1/billing/checkout/preview/
POST /api/v1/billing/checkout/create/
GET  /api/v1/billing/subscription/me/
POST /api/v1/billing/subscription/create/
POST /api/v1/billing/subscription/cancel/
POST /api/v1/billing/subscription/change-plan/
GET  /api/v1/billing/payments/
POST /api/v1/billing/webhooks/asaas/
```

Também existe alias sem versão para compatibilidade com o prompt do checkout:

```http
GET  /api/billing/plans/
POST /api/billing/checkout/preview/
POST /api/billing/checkout/create/
POST /api/billing/webhooks/asaas/
```

### Preview do checkout

```json
{
  "plan_slug": "profissional",
  "type": "SUBSCRIPTION",
  "billingType": "PIX",
  "dueDate": "2026-07-10",
  "description": "Assinatura Elo Terapêutico - Profissional"
}
```

Resposta inclui:

- `gateway`: sempre `ASAAS`.
- `environment`: `SANDBOX` ou `PRODUCTION`.
- `notice`: “Os pagamentos serão processados pelo Asaas.”
- `activation_rule`: reforça que a ativação depende do webhook.
- `plan`: plano serializado do backend.
- `checkout`: payload normalizado com `billingType`, `dueDate`, `value`, `cycle` e `installmentCount`.

### Criar checkout

```json
{
  "plan_slug": "profissional",
  "type": "SUBSCRIPTION",
  "billingType": "BOLETO",
  "dueDate": "2026-07-10",
  "description": "Assinatura Elo Terapêutico - Profissional"
}
```

Para `SUBSCRIPTION`, o backend cria `customer` e `subscription` no Asaas e salva a assinatura local como `PENDING`.

Para `ONE_TIME`, o backend usa `create_payment(user, checkout_data)` no Asaas. Parcelamento é aceito apenas nesse tipo por `installmentCount`.

### Criar assinatura legada

```json
{
  "plan_id": 1
}
```

Essa rota continua disponível para compatibilidade interna, mas o fluxo recomendado do produto é `/checkout?plan=<slug>`.

### Trocar plano

```json
{
  "plan_id": 2
}
```

Na primeira versão, a troca cancela a assinatura atual e cria uma nova assinatura no gateway, sem cálculo proporcional de upgrade/downgrade.

## Frontend

Rotas principais:

- `/` — landing page pública com seção **Planos**.
- `/planos` — listagem pública/autenticada de planos.
- `/checkout?plan=profissional` — wizard de checkout Asaas.
- `/billing/pendente` — acompanhamento de assinatura pendente.
- `/dashboard/configuracoes/assinatura` — gestão de assinatura.
- `/dashboard/configuracoes/faturas` — faturas do usuário.

A landing não duplica preços hardcoded. Ela consome `GET /api/v1/billing/plans/`. Se a API falhar, exibe um fallback visual simples sem travar a página.

## Features por plano

Mapeamento:

| Feature | Campo do plano |
| --- | --- |
| agenda | `has_agenda` |
| patients | `has_patients` |
| clinical_records | `has_clinical_records` |
| financial | `has_financial` |
| documents | `has_documents` |
| forms | `has_forms` |
| reports | `has_reports` |
| ai | `has_ai` |

Serviços principais:

- `has_feature(user, feature_key)`
- `can_use_feature(user, feature_key)`
- `get_plan_limits(user)`
- `enforce_patient_limit(user)`

O limite inicial implementado é `max_patients`. Dados clínicos já cadastrados não são apagados quando o plano muda, atrasa ou é cancelado.

## Planos iniciais

A migration `0002_seed_initial_plans` cria:

- Essencial
- Profissional
- Premium

Os valores são sementes iniciais e podem ser ajustados pelo Admin.

## Como testar localmente

1. Configure `.env` com credenciais do Asaas Sandbox.
2. Rode migrations:

```bash
cd backend
python manage.py migrate
```

3. Suba backend e frontend.
4. Exponha o backend local com ngrok ou alternativa semelhante:

```bash
ngrok http 8000
```

5. Cadastre no Asaas Sandbox a URL:

```text
https://SEU_SUBDOMINIO.ngrok-free.app/api/v1/billing/webhooks/asaas/
```

6. Configure o token de webhook no Asaas e no `.env`.
7. Acesse `/`, escolha um plano, faça cadastro/login e finalize `/checkout?plan=<slug>`.
8. Simule/confirme um pagamento no painel sandbox do Asaas.
9. Confirme que a assinatura local saiu de `PENDING` para `ACTIVE` após webhook.

## Segurança e LGPD

- Não armazenar número de cartão, CVV ou dados sensíveis de pagamento.
- Não enviar dados clínicos para o gateway.
- Armazenar apenas IDs, status, URLs de fatura/boleto e payloads necessários para auditoria financeira.
- O frontend nunca ativa assinatura sozinho.
- A ativação paga acontece somente por webhook validado no backend.
- Usuários só acessam os próprios pagamentos.

## Próximos passos

- Implementar checkout/tokenização segura para `CREDIT_CARD`.
- Adicionar cobrança proporcional para troca de plano.
- Implementar limites de documentos, armazenamento e uso de IA.
- Adicionar alertas internos para `PAST_DUE` e cancelamentos.
