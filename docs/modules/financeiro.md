# Especificação técnica — Módulo Financeiro

## Identidade técnica

- package Python: `apps.finances`;
- app label Django: `financeiro`;
- API canônica: `/api/v1/finances/`;
- nome visual: Financeiro.

## Entidades

- `FinancialTransaction`: receitas, despesas, pagamentos, cancelamentos e estornos;
- `MonthlySubscription`: mensalidade recorrente de paciente, distinta da assinatura SaaS.

## Arquitetura

```text
api/v1 → services/selectors → models
```

Views e serializers não acessam ORM. Services centralizam transações de banco e selectors centralizam consultas e isolamento por profissional.

## Transições

- pendente/parcial → pago;
- pendente/parcial → cancelado;
- pago → estornado.

Pagamentos parciais atualizam `paid_amount` e preservam o saldo em aberto.

## Segurança

O terapeuta só acessa seus lançamentos. Paciente, consulta e mensalidade devem pertencer ao mesmo profissional. Exportações respeitam o escopo e sanitizam células contra CSV Injection.
