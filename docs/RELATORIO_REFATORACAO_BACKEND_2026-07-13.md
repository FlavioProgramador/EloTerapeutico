# Relatório da reorganização do backend Django

## 1. Estrutura anterior

- pacote transversal em `backend/core`, fora de `backend/apps`;
- possibilidade de confusão entre o namespace `core` e os apps de domínio;
- configuração Django concentrada em `backend/elo_terapeutico`;
- client HTTP do Asaas dentro da camada de services de billing;
- views de billing com consultas ORM complexas e chamadas diretas ao adapter externo;
- integração de e-mail duplicada entre core e infrastructure;
- referências aos namespaces antigos espalhadas por código, testes, migrations, Docker, scripts, CI e documentação;
- ausência de uma verificação automatizada para impedir regressões estruturais.

## 2. Estrutura final

```text
backend/
├── apps/
│   ├── core/
│   │   ├── api/
│   │   └── tests/
│   ├── audit/
│   │   └── services/
│   └── billing/
│       ├── selectors/
│       ├── services/
│       └── tests/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── infrastructure/
│   ├── messaging/
│   └── payments/asaas/
└── quality/
    └── check_backend_architecture.py
```

- core canônico em `backend/apps/core`, com o label Django `core` preservado;
- configuração centralizada em `backend/config`;
- integração Asaas em `backend/apps/billing/infrastructure/payments/asaas/client.py`;
- logging de acesso sensível no domínio de auditoria;
- mensageria de e-mail consolidada em `backend/apps/communications/infrastructure/messaging`;
- validação arquitetural executável em `backend/apps/core/quality/check_backend_architecture.py`.

## 3. Tratamento do core externo

- `audit.py` foi classificado como responsabilidade do domínio de auditoria e movido para `apps/audit/services/access_logging.py`;
- `integrations/notifications.py` foi classificado como infraestrutura de mensageria e consolidado em `infrastructure/messaging/email.py`;
- `pagination.py` foi movido para `apps/core/api/pagination.py`;
- exceptions, validators, fields, segurança e componentes transversais do admin permaneceram no core canônico;
- testes do core permaneceram próximos ao app;
- `backend/core` foi removido integralmente;
- `backend/elo_terapeutico` foi substituído por `backend/config`;
- imports antigos foram atualizados sem aliases permanentes.

## 4. Apps reorganizados

- `core`: pacote transversal canônico, paginação, segurança, exceptions, validators e testes arquiteturais;
- `audit`: service transversal de logging de acesso;
- `billing`: regras de negócio, services, selectors e portas de gateway;
- os demais apps tiveram imports e referências de configuração corrigidos, sem alteração de labels, tabelas ou contratos públicos.

## 5. Services criados ou movidos

- `apps.billing.services.integration_health.get_billing_integration_health` passou a orquestrar health check do gateway e estatísticas de webhooks;
- `apps.billing.services.payment_sync.refresh_gateway_payment` passou a coordenar a sincronização de uma cobrança;
- a porta e as exceções do gateway permanecem no domínio `billing`;
- a implementação HTTP do Asaas passou para infrastructure;
- tasks, views e endpoints continuam delegando casos de uso aos services existentes.

O fluxo de pagamento ficou explicitamente:

```text
View → Service de billing → Adapter da infrastructure → API do Asaas
```

## 6. Views refatoradas

Foram refatoradas:

- `apps.billing.checkout_views.CheckoutCreateView`;
- `apps.billing.checkout_views.BillingIntegrationHealthView`;
- `apps.billing.views.PlanListView`;
- `apps.billing.views.PlanPriceListView`;
- `apps.billing.views.CheckoutCreateView`;
- `apps.billing.views.BillingOrderListView`;
- `apps.billing.views.BillingOrderDetailView`;
- `apps.billing.views.PaymentListView`;
- `apps.billing.views.PaymentDetailView`;
- `apps.billing.views.PaymentRefreshView`;
- `apps.billing.views.PaymentSummaryView`;
- `apps.billing.views.BillingIntegrationHealthView`.

Essas views não importam mais `infrastructure` diretamente e não acessam mais `.objects`. Permanecem responsáveis apenas por autenticação, validação, serializers, status HTTP e chamada de services/selectors.

## 7. Selectors criados

- `selectors/catalog.py`: planos e preços ativos;
- `selectors/orders.py`: pedidos do usuário e carregamento otimizado de pedido com pagamentos;
- `selectors/payments.py`: listagem, detalhe para sincronização e resumo financeiro por usuário;
- `selectors/integrations.py`: estatísticas de processamento de webhooks.

Os selectors de pedidos e pagamentos aplicam o usuário autenticado como filtro obrigatório, evitando depender de IDs enviados pelo frontend como proteção de tenant.

## 8. Configurações e infraestrutura atualizadas

Foram atualizados:

- settings, URLs, ASGI, WSGI e `manage.py`;
- Dockerfiles, Docker Compose, Gunicorn e scripts de inicialização;
- pytest e referências de ambiente;
- workflows de Django, billing e segurança;
- documentação de estrutura de pastas;
- imports em código, testes, migrations e comandos.

Os settings agora utilizam `config.settings.base`, `config.settings.development`, `config.settings.production` e `config.settings.test`.

## 9. Testes e validação

Foram adicionados ou atualizados:

- teste de unicidade do app `core`;
- teste de ausência dos pacotes legados;
- teste de fronteira impedindo views de billing de importar infrastructure ou acessar ORM diretamente;
- teste de escopo de tenant no selector de pagamentos;
- testes do service de sincronização de cobrança;
- verificador estático de imports, diretórios proibidos, destinos obrigatórios e fronteira HTTP de billing.

Resultados obtidos durante a implementação:

- `python manage.py check`: aprovado;
- `python manage.py makemigrations --check --dry-run`: aprovado;
- suíte completa após a reorganização estrutural: **327 testes aprovados**;
- quatro testes direcionados da separação final de billing: aprovados;
- Ruff: aprovado após organização dos imports;
- Bandit: zero problemas identificados;
- `pip-audit`: nenhuma vulnerabilidade identificada;
- validação arquitetural e `compileall`: aprovados;
- builds e checks de billing, frontend e documentação: aprovados nas rodadas executadas.

A rodada final dos workflows do Pull Request continua sendo a fonte de verdade para o merge.

## 10. Migrations, compatibilidade e pendências

- nenhuma migration foi apagada, recriada ou reordenada;
- arquivos de migration tiveram apenas imports Python atualizados quando apontavam para namespaces removidos;
- operações de migration, estado do banco, nomes de tabelas, constraints, índices e app labels foram preservados;
- nenhum model foi transferido entre apps Django;
- endpoints e contratos consumidos pelo frontend foram preservados;
- não foi criado alias permanente para `core` ou `elo_terapeutico`;
- não existe mais `core/` na raiz, `backend/core/` ou `backend/elo_terapeutico/`;
- o Pull Request permanece em draft e não deve ser mesclado enquanto algum workflow obrigatório estiver pendente ou com falha.
