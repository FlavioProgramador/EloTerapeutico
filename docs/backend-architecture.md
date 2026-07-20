# Arquitetura do backend

## Fluxo canônico

```text
URLs
  ↓
Views / ViewSets
  ↓
Serializers · Filters · Permissions
  ↓
Services · Selectors
  ↓
Models
```

Models não conhecem HTTP. Selectors são somente leitura. Services representam casos de uso, recebem argumentos nomeados e usam `transaction.atomic` e `select_for_update()` quando há concorrência.

## Isolamento multi-tenant

Toda leitura ou alteração deve restringir o conjunto de dados antes de buscar por ID. Relações recebidas em payload devem pertencer ao mesmo profissional.

## Domínios financeiros

`apps.finances` controla receitas, despesas, pagamentos, mensalidades de pacientes e cobranças de consultas. O package é inglês, mas o app label histórico permanece `financeiro`.

`apps.billing` controla planos, checkout, assinatura SaaS e gateways comerciais do Elo Terapêutico.

## Imports e migrations

Exports públicos usam `__all__` explícito. `import *` é proibido. Migrations históricas não são reescritas durante reorganizações de packages.

## Validação

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python apps/core/quality/check_backend_architecture.py
pytest --create-db
ruff check .
mypy .
```
