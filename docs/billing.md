# Billing e Assinaturas

O módulo de Billing gerencia planos, assinaturas e pagamentos da assinatura do terapeuta no Elo Terapêutico. Ele não processa pagamentos de pacientes e não envia dados clínicos ao gateway.

## Visão geral

Fluxo inicial:

1. O terapeuta acessa `/planos` ou `/dashboard/configuracoes/assinatura`.
2. O frontend lista planos ativos em `GET /api/v1/billing/plans/`.
3. O usuário autenticado escolhe um plano em `POST /api/v1/billing/subscription/create/`.
4. O backend cria customer e subscription no Asaas Sandbox.
5. A assinatura local fica como `TRIALING` quando houver trial ou `PENDING` quando não houver trial.
6. A liberação definitiva do plano pago ocorre pelo webhook `PAYMENT_CONFIRMED` ou `PAYMENT_RECEIVED`.
7. Os módulos são liberados conforme as flags do plano.

## Variáveis de ambiente

```env
ASAAS_API_KEY=
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
ASAAS_WEBHOOK_TOKEN=dev-webhook-token
BILLING_TRIAL_DAYS=7
BILLING_DEFAULT_CURRENCY=BRL
```

Regras:

- Nunca versionar chave real do Asaas.
- Em desenvolvimento, usar `https://api-sandbox.asaas.com/v3`.
- Em produção, `ASAAS_BASE_URL` não pode conter `sandbox`.
- `ASAAS_WEBHOOK_TOKEN` deve ser configurado em produção.

## Webhook Asaas

Endpoint:

```http
POST /api/v1/billing/webhooks/asaas/
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
GET  /api/v1/billing/subscription/me/
POST /api/v1/billing/subscription/create/
POST /api/v1/billing/subscription/cancel/
POST /api/v1/billing/subscription/change-plan/
GET  /api/v1/billing/payments/
POST /api/v1/billing/webhooks/asaas/
```

### Criar assinatura

```json
{
  "plan_id": 1
}
```

### Trocar plano

```json
{
  "plan_id": 2
}
```

Na primeira versão, a troca cancela a assinatura atual e cria uma nova assinatura no gateway, sem cálculo proporcional de upgrade/downgrade.

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
7. Crie uma assinatura pelo frontend e simule/confirme um pagamento no painel sandbox.

## Segurança e LGPD

- Não armazenar número de cartão, CVV ou dados sensíveis de pagamento.
- Não enviar dados clínicos para o gateway.
- Armazenar apenas IDs, status, URLs de fatura/boleto e payloads necessários para auditoria financeira.
- O frontend nunca ativa assinatura sozinho.
- A ativação paga acontece somente por webhook validado no backend.
- Usuários só acessam os próprios pagamentos.

## Próximos passos

- Implementar portal/link de pagamento conforme decisão final do checkout Asaas.
- Adicionar cobrança proporcional para troca de plano.
- Implementar limites de documentos, armazenamento e uso de IA.
- Adicionar alertas internos para `PAST_DUE` e cancelamentos.
