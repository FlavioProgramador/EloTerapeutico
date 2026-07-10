# Endpoints — Billing

Base oficial: `/api/v1/billing/`. O alias legado `/api/billing/` deve ser mantido somente durante a transição.

## Catálogo

### GET `plans/`

Público. Lista planos ativos, recursos e opções comerciais aninhadas em `prices`.

### GET `plan-prices/`

Público. Lista preços ativos. Filtros aceitos:

- `plan=<slug>`;
- `billing_interval=MONTHLY|YEARLY`;
- `billing_model=RECURRING|ONE_TIME|INSTALLMENT`.

## Checkout

### POST `checkout/preview/`

JWT. Valida preço, CPF/CNPJ, forma de pagamento e quantidade de parcelas sem criar cobrança.

Exemplo:

```json
{
  "plan_price_id": 10,
  "billingType": "BOLETO",
  "cpfCnpj": "529.982.247-25",
  "dueDate": "2026-07-15",
  "installmentCount": 12
}
```

O valor retornado sempre vem de `PlanPrice`; valores arbitrários enviados pelo cliente são ignorados.

### POST `checkout/create/`

JWT. Cria `BillingOrder`, cobrança no Asaas, assinatura pendente quando aplicável e sincroniza as faturas disponíveis.

Envie a chave também no header:

```http
Idempotency-Key: 2f5314a0-73a5-41f6-87e8-907dbd966568
```

A mesma chave para o mesmo usuário retorna a contratação existente sem duplicar a cobrança.

Resposta principal:

```json
{
  "order": {},
  "subscription": {},
  "payments": [],
  "status": "PENDING"
}
```

Falhas controladas do gateway retornam `502`. Acesso somente é liberado por confirmação processada no backend.

## Assinatura

### GET `subscription/me/`

JWT. Retorna assinatura operacional atual ou `null`, incluindo contratação, período, carência e cancelamento agendado.

### POST `subscription/create/`

JWT. Endpoint legado. Cria assinatura para um plano usando a opção comercial compatível. Novas interfaces devem usar o checkout.

### POST `subscription/cancel/`

JWT. Cancelamento imediato explícito. Não realiza estorno automático.

### POST `subscription/cancel-at-period-end/`

JWT. Agenda cancelamento e mantém acesso até o fim do período.

### POST `subscription/resume/`

JWT. Remove o cancelamento agendado antes do encerramento.

### POST `subscription/change-plan/`

JWT. Registra intenção de troca sem cancelar o plano atual. A alteração efetiva depende do novo checkout e da confirmação do pagamento.

## Contratações

### GET `orders/`

JWT. Lista contratações do usuário autenticado.

### GET `orders/{public_id}/`

JWT. Retorna uma contratação pelo UUID público. O queryset é limitado ao proprietário.

## Faturas

### GET `payments/`

JWT. Lista faturas do usuário. Filtros:

- `status`;
- `order=<uuid>`;
- `ordering=due_date|-due_date|created_at|-created_at|status|-status`.

Cada item contém `installment_number`, `installment_count` e `installment_label`.

### GET `payments/summary/`

JWT. Retorna total contratado, total pago, parcelas pagas, quantidade total, próximo vencimento e número de parcelas vencidas.

Aceita `order=<uuid>`.

### GET `payments/{id}/`

JWT. Detalhe de uma fatura pertencente ao usuário.

### POST `payments/{id}/refresh/`

JWT. Consulta a cobrança no Asaas e atualiza o registro local.

## Integração

### GET `integrations/asaas/health/`

Somente administrador. Verifica conectividade sem criar cobrança e retorna ambiente, último webhook e contadores de eventos pendentes/falhos.

## Webhook

### POST `webhooks/asaas/`

Sem JWT. Exige token compartilhado quando configurado.

Headers aceitos incluem:

```http
asaas-access-token: <token-configurado>
Content-Type: application/json
```

O endpoint:

1. valida o token;
2. persiste payload sanitizado;
3. deduplica por ID/hash;
4. processa o evento;
5. agenda retry quando a contratação ainda não pode ser localizada;
6. retorna `200` para eventos recebidos, inclusive desconhecidos registrados como ignorados.

## Segurança

- não envie `ASAAS_API_KEY` ao frontend;
- cartão exige tokenização ou checkout hospedado oficial;
- não envie preço confiável pelo navegador;
- não persista cartão, CVV, token ou payload sensível;
- endpoints autenticados filtram por usuário;
- nenhum dado clínico deve ser enviado ao gateway.

[Voltar à API](../README.md)
