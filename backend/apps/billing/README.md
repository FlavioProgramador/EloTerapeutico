# Billing app

O app `billing` concentra catálogo comercial, checkout, contratações, assinaturas, pagamentos, entitlement, uso de recursos e integração com o Asaas.

## Estrutura canônica

```text
billing/
├── admin/
├── api/
│   ├── access/
│   │   └── decorators.py
│   ├── authentication/
│   │   └── __init__.py
│   ├── legacy/
│   │   ├── routes.py
│   │   └── urls.py
│   ├── public/
│   │   ├── serializers/
│   │   ├── views/
│   │   │   ├── registration.py
│   │   │   └── webhooks.py
│   │   └── urls.py
│   └── v1/
│       ├── permissions/
│       ├── serializers/
│       ├── views/
│       └── urls.py
├── integrations/
│   └── asaas/
│       ├── webhooks/
│       │   ├── constants.py
│       │   ├── identifiers.py
│       │   ├── orders.py
│       │   ├── payments.py
│       │   ├── persistence.py
│       │   ├── processor.py
│       │   └── subscriptions.py
│       ├── client.py
│       ├── exceptions.py
│       └── security.py
├── management/commands/
├── migrations/
├── models/
├── selectors/
├── services/
├── tasks/
├── tests/
├── README.md
├── __init__.py
└── apps.py
```

A raiz do app possui somente os entrypoints obrigatórios. Implementações, compatibilidades e configurações permanecem em pacotes específicos.

## Responsabilidades

### Models

As entidades são separadas por contexto:

- `models/catalog.py`: `Plan` e `PlanPrice`;
- `models/orders.py`: `BillingOrder`;
- `models/subscriptions.py`: `Subscription`;
- `models/payments.py`: `Payment`;
- `models/webhooks.py`: `WebhookEvent`;
- `models/usage.py`: `FeatureUsage`.

O pacote `models/__init__.py` preserva os imports públicos, labels Django, nomes das tabelas e histórico das migrations.

### API autenticada

A API operacional está em `api/v1`:

- catálogo e preços;
- preview e criação de checkout;
- contratações;
- assinatura atual, cancelamento e troca de plano;
- pagamentos e sincronização;
- entitlement;
- health check administrativo da integração.

Views tratam HTTP, validam o contrato por serializers e delegam para services e selectors. Não devem acessar o ORM nem o client do gateway diretamente.

### API pública

Endpoints sem autenticação de sessão ficam em `api/public`:

- cadastro de usuário vinculado a plano ou teste gratuito;
- recebimento do webhook do Asaas.

As rotas públicas são declaradas em `api/public/urls.py` e incorporadas ao contrato `/api/v1/billing/` sem criar um namespace adicional ou alterar os nomes históricos das URLs.

### Autenticação e acesso

- `api/authentication`: autenticação JWT com sessão revogável e validação de entitlement;
- `api/access`: decorators de autorização por funcionalidade do plano;
- `api/v1/permissions`: permissions específicas dos endpoints de Billing.

Os caminhos antigos permanecem apenas como fachadas finas enquanto settings e consumidores legados são migrados.

### Services e selectors

- services coordenam casos de uso, alterações de estado, transações e chamadas ao gateway;
- selectors concentram leituras, filtros e isolamento por usuário;
- services não dependem de `Request`, `Response` ou classes de view;
- selectors não realizam efeitos colaterais.

## Integração com o Asaas

A integração canônica está em `integrations/asaas`:

- `client.py`: transporte HTTP, autenticação, timeouts e normalização de payloads;
- `exceptions.py`: contrato público das falhas do provider;
- `security.py`: sanitização de dados sensíveis do gateway;
- `webhooks/`: interpretação e persistência dos eventos externos.

O `__init__.py` do provider não importa webhooks antecipadamente. Essa restrição evita ciclos entre o client, services de cobrança e processamento de pagamentos.

Código novo deve importar diretamente:

```python
from apps.billing.integrations.asaas.client import AsaasGateway
from apps.billing.integrations.asaas.webhooks import process_webhook_event
```

## Fluxo de checkout

```text
API
  ↓
serializer valida preço, documento e idempotência
  ↓
service cria ou reutiliza BillingOrder
  ↓
client Asaas cria cliente e cobrança
  ↓
assinatura e pagamentos permanecem pendentes
  ↓
webhook ou reconciliação confirma o estado financeiro
  ↓
entitlement libera ou bloqueia o acesso
```

A confirmação do gateway é a fonte de verdade. O frontend não ativa assinaturas diretamente.

## Webhooks

O processamento é dividido em:

- `constants.py`: mapeamento de eventos para status;
- `identifiers.py`: identificação e hash idempotente;
- `orders.py`: localização da contratação e atualização financeira;
- `payments.py`: eventos de pagamento;
- `subscriptions.py`: eventos de assinatura;
- `persistence.py`: persistência, retry e finalização;
- `processor.py`: orquestração da entrada pública e do worker.

Eventos são persistidos antes do processamento. O fluxo preserva idempotência, lock transacional, retry limitado e sanitização de payloads.

## Tasks

As tasks estão separadas em:

- `tasks/webhooks.py`;
- `tasks/reconciliation.py`.

Os nomes Celery permanecem estáveis:

```text
apps.billing.tasks.process_webhook_event
apps.billing.tasks.dispatch_pending_webhook_events
apps.billing.tasks.reconcile_asaas_payments
```

## Compatibilidade temporária

Os seguintes caminhos existem somente como fachadas de transição:

- `authentication/`;
- `security/`;
- `views/`;
- `webhooks/asaas.py`;
- `infrastructure/payments/asaas/client.py`;
- `integrations/webhooks/asaas/`;
- `api/public/registration.py`;
- `api/public/webhooks.py`;
- `api/v1/authentication.py`;
- `api/v1/decorators.py`.

Esses arquivos não devem receber novas regras de negócio. Novos consumidores devem utilizar os pacotes canônicos. A remoção das fachadas só pode ocorrer após busca global, migração dos imports, validação das referências por string e uma versão de transição sem consumidores.

## Regras de dependência

```text
api → serializers/permissions → services/selectors → models
services → integrations/asaas/client
webhooks/tasks/commands → services
```

É proibido:

- models importarem API, tasks ou integrações;
- views acessarem ORM ou infraestrutura diretamente;
- services dependerem de objetos HTTP;
- provider importar webhooks antecipadamente no pacote raiz;
- duplicar implementação entre caminhos canônicos e fachadas legadas.

## Validação

```bash
python apps/core/quality/check_backend_architecture.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
pytest apps/billing/tests -q --tb=short
pytest -q
ruff check apps/billing apps/core
```

A suíte `tests/test_canonical_architecture.py` protege a estrutura canônica, limita o tamanho das fachadas e impede o retorno do ciclo de imports do provider.

Documentação complementar:

```text
docs/05-modulos/billing/README.md
docs/07-api/endpoints/billing.md
docs/backend/app-architecture.md
```
