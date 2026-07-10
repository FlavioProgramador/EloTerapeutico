# Módulo de billing e assinatura

**Status: implementado; requer Asaas e webhook configurados.**

## Finalidade

Cobrar o uso do Elo Terapêutico por planos, controlar assinatura, pagamentos e acesso a recursos. Não confundir com o financeiro dos pacientes.

## Entidades

### Plan

Preço, moeda, ciclo mensal/anual, limites de pacientes/storage e flags de recursos: agenda, pacientes, prontuário, financeiro, documentos, formulários, relatórios e IA.

### Subscription

Status: `TRIALING`, `PENDING`, `ACTIVE`, `PAST_DUE`, `CANCELED`, `EXPIRED`. Vincula usuário, plano, períodos e IDs Asaas.

### Payment

Status: `PENDING`, `CONFIRMED`, `RECEIVED`, `OVERDUE`, `REFUNDED`, `CANCELED`, `FAILED`. Armazena valores, URLs públicas necessárias, IDs e payload sanitizado.

### WebhookEvent e FeatureUsage

Eventos são deduplicados por ID/hash e registram processamento. Uso de recurso é agregado por período.

## Regras

- planos públicos listam apenas ativos;
- frontend não ativa plano;
- assinatura fica pendente até confirmação por webhook;
- produção rejeita URL sandbox e exige API key/token fortes;
- cartão exige tokenização; dados brutos de cartão não são aceitos como fluxo padrão;
- respostas do checkout expõem somente campos públicos necessários;
- erros do gateway retornam mensagem controlada e `502`;
- pagamentos e assinatura são filtrados pelo usuário;
- eventos repetidos devem ser idempotentes.

## API

Prefixo principal `/api/v1/billing/`:

- `plans/` pública;
- `checkout/preview/`;
- `checkout/create/`;
- `subscription/me/`;
- `subscription/create/`;
- `subscription/cancel/`;
- `subscription/change-plan/`;
- `payments/`;
- `webhooks/asaas/` pública com token no header.

Também existe `/api/billing/` apontando para as mesmas URLs. Essa duplicidade deve ser consolidada futuramente.

## Frontend

Páginas de checkout, upgrade, sucesso, pendência, assinatura e faturas. `checkout-wizard.tsx` conduz o fluxo.

## Segurança

- chave Asaas só no backend;
- token do webhook comparado com `secrets.compare_digest`;
- payload sensível é redigido antes de persistência/diagnóstico;
- produção não inicia sem webhook token forte;
- sem token em desenvolvimento, o webhook é aceito com warning — nunca exponha esse cenário;
- URLs de boleto/fatura são dados do usuário e não devem vazar.

## Testes

Há testes de checkout, assinaturas, gateway, erros, redaction e segurança do webhook.

## Limitações

- disponibilidade depende do Asaas;
- reconciliação e chargebacks exigem operação;
- não há PCI próprio; cartão deve permanecer tokenizado pelo provedor;
- flags de plano exigem enforcement consistente em todos os módulos;
- billing não gera automaticamente escrituração financeira clínica completa.

[Voltar aos módulos](../README.md)
