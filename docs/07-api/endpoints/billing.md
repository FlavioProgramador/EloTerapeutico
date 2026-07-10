# Endpoints — Billing

Base principal: `/api/v1/billing/`. Existe alias legado `/api/billing/`.

## GET `plans/`

Público. Lista planos ativos.

## POST `checkout/preview/`

JWT. Valida plano e checkout sem criar cobrança.

## POST `checkout/create/`

JWT. Cria assinatura ou cobrança única. Retorna 201; falha de gateway retorna 502 controlado. O status de assinatura permanece pendente até webhook.

## GET `subscription/me/`

JWT. Retorna assinatura atual ou `null`.

## POST `subscription/create/`

JWT. Cria assinatura para plano validado.

## POST `subscription/cancel/`

JWT. Cancela a assinatura do próprio usuário.

## POST `subscription/change-plan/`

JWT. Troca o plano por fluxo coordenado.

## GET `payments/`

JWT. Lista pagamentos do usuário.

## POST `webhooks/asaas/`

Sem JWT. Exige token compartilhado em um dos headers aceitos quando configurado. Deduplica e processa evento.

Exemplo de headers:

```http
asaas-access-token: <token-configurado>
Content-Type: application/json
```

## Segurança

Não envie `ASAAS_API_KEY` ao frontend. Cartão só por tokenização. Não persista CPF, token ou payload bruto sem redaction. Produção exige token de webhook forte e URL não-sandbox.

[Voltar à API](../README.md)
