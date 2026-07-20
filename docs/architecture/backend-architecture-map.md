# Mapa arquitetural do backend

## Grafo de dependências

```text
URLs → Views → Serializers/Filters/Permissions → Services/Selectors → Models
```

Integrações externas seguem `View → Service → Integration/Gateway`.

## Domínios técnicos

- `apps.scheduling` preserva `label=agenda`;
- `apps.finances` preserva `label=financeiro`;
- `apps.billing` permanece responsável pela assinatura SaaS;
- `apps.finances` permanece responsável pelas finanças clínicas do profissional.

## Estrutura de finances

```text
finances/
├── admin/
├── api/v1/
├── exceptions/
├── integrations/
├── migrations/
├── models/
├── selectors/
├── services/
├── tests/
├── README.md
├── __init__.py
└── apps.py
```

Views e serializers não acessam ORM. Services controlam transações e selectors controlam consultas e isolamento multi-tenant.

## Compatibilidade

A reorganização de packages Python não altera app labels históricos, tabelas, migrations, permissões, ContentTypes ou identificadores persistidos.
