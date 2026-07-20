# Módulo financeiro

**Status: implementado.**

Controla receitas, despesas e mensalidades da atividade do profissional. Este domínio é diferente do billing da assinatura do Elo Terapêutico.

## Entidades

- `FinancialTransaction`: receita ou despesa do profissional;
- `MonthlySubscription`: mensalidade de paciente, não assinatura SaaS.

## API

A API canônica está em `/api/v1/finances/` e preserva CRUD, pagamentos, cancelamentos, estornos, resumos, exportações, mensalidades e geração de cobranças por consulta.

## Backend

O package Python é `apps.finances`, mas o app label histórico permanece `financeiro` para preservar banco, migrations, permissões e URLs administrativas.

## Frontend

A feature e o nome visual continuam `features/financeiro` e “Financeiro”.
