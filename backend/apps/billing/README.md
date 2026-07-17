# Billing app

O app `billing` concentra catálogo comercial, checkout, contratações, assinaturas, pagamentos, entitlement, uso de recursos, integração com o Asaas e processamento de webhooks.

## Estrutura interna

```text
billing/
├── api/
│   ├── v1/
│   │   ├── serializers/
│   │   ├── views/
│   │   ├── permissions/
│   │   ├── authentication.py
│   │   ├── decorators.py
│   │   └── urls.py
│   └── public/
│       ├── serializers/
│       ├── registration.py
│       └── webhooks.py
├── admin/
├── integrations/
│   └── webhooks/asaas/
├── infrastructure/
│   └── payments/asaas/
├── models/
├── selectors/
├── services/
├── tasks/
├── webhooks/
├── management/commands/
├── migrations/
└── tests/
```

## Models

As entidades foram separadas por contexto:

- `models/catalog.py`: `Plan` e `PlanPrice`;
- `models/orders.py`: `BillingOrder`;
- `models/subscriptions.py`: `Subscription`;
- `models/payments.py`: `Payment`;
- `models/webhooks.py`: `WebhookEvent`;
- `models/usage.py`: `FeatureUsage`.

O pacote `models/__init__.py` preserva os imports públicos de `apps.billing.models`, os labels Django, os nomes das tabelas e o estado das migrations.

## API

A implementação canônica está em `api/v1`:

- catálogo e preços;
- preview e criação de checkout;
- contratações;
- assinaturas e troca de plano;
- pagamentos e sincronização;
- entitlement;
- health check administrativo da integração.

Endpoints públicos, como cadastro por plano e webhook do Asaas, estão em `api/public`.

Os arquivos `views.py`, `checkout_views.py`, `access_views.py`, `serializers.py`, `permissions.py`, `authentication.py`, `decorators.py`, `registration.py` e `urls.py` permanecem como fachadas finas para preservar contratos internos existentes.

## Checkout

```text
API
  ↓
serializer valida plano, documento e idempotência
  ↓
service de checkout cria ou reutiliza a contratação
  ↓
adapter Asaas cria cliente e cobrança
  ↓
pagamentos e assinatura permanecem pendentes
  ↓
webhook ou reconciliação confirma o estado financeiro
```

A ativação do acesso não depende do frontend. A confirmação do gateway, recebida por webhook ou reconciliação, é a fonte de verdade.

## Webhooks do Asaas

A integração foi dividida em `integrations/webhooks/asaas`:

- `constants.py`: mapeamento de eventos para status;
- `identifiers.py`: id e hash idempotente;
- `orders.py`: localização de contratação e atualização financeira;
- `payments.py`: processamento de eventos de pagamento;
- `subscriptions.py`: processamento de eventos de assinatura;
- `persistence.py`: persistência, retry e finalização dos eventos;
- `processor.py`: orquestração e entrada do webhook.

`webhooks/asaas.py` permanece como fachada para preservar imports e pontos de monkeypatch usados pela suíte histórica.

## Tasks

As tasks estão separadas em:

- `tasks/webhooks.py`;
- `tasks/reconciliation.py`.

Os nomes públicos registrados no Celery foram preservados:

```text
apps.billing.tasks.process_webhook_event
apps.billing.tasks.dispatch_pending_webhook_events
apps.billing.tasks.reconcile_asaas_payments
```

## Camadas

- views tratam HTTP e delegam operações;
- serializers validam o contrato de entrada e saída;
- selectors concentram leituras e isolamento por usuário;
- services coordenam regras de negócio e transações;
- infrastructure contém o client HTTP do gateway;
- integrations interpretam eventos externos;
- tasks são entradas assíncronas finas.

## Validação

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest backend/apps/billing backend/apps/core/tests/project/test_api_architecture.py
python backend/apps/core/quality/check_backend_architecture.py
ruff check backend/apps/billing backend/apps/core
```

Documentação complementar:

```text
docs/05-modulos/billing/README.md
docs/07-api/endpoints/billing.md
docs/backend/app-architecture.md
```
