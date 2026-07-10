# Endpoints — Financeiro

Base: `/api/v1/financeiro/`, registrada por `TransactionViewSet`.

## Operações

- CRUD de transações;
- filtros/listas;
- alteração de estados;
- registrar pagamento parcial/integral;
- cancelar e estornar;
- mensalidades;
- resumos de dashboard;
- relatórios e exportações;
- integrações auxiliares de billing conforme actions.

## Payload conceitual

```json
{
  "transaction_type": "income",
  "category": "session",
  "amount": "150.00",
  "payment_status": "pending",
  "due_date": "2026-07-20",
  "patient": 101,
  "description": "Sessão fictícia para documentação"
}
```

## Regras

Valor deve ser positivo; `paid_amount` não supera total; recorrência exige frequência; transição precisa ser permitida; referências devem pertencer ao escopo do terapeuta.

O schema OpenAPI é a fonte para URL exata das actions do ViewSet.

[Voltar à API](../README.md)
