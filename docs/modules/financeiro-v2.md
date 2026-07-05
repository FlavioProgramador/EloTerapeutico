# Módulo Financeiro — Painel Operacional

A evolução organiza o financeiro em **A Receber**, **A Pagar** e **Mensalidades**, com cards de recebido, pendências, vencidos e saldo projetado.

## Regras

- Todo lançamento respeita o profissional autenticado.
- Dinheiro usa `DecimalField`.
- Cobranças de sessões são idempotentes.
- Mensalidades usam os estados `active`, `paused`, `ended` e `cancelled`.
- Pagamentos podem ser totais ou parciais.
- Links de pagamento devem usar HTTPS.

```text
saldo projetado = recebido + a receber - despesas pagas - a pagar
```

## Endpoints

- `GET /api/v1/financeiro/summary/`
- `GET|POST /api/v1/financeiro/`
- `PATCH /api/v1/financeiro/{id}/pay/`
- `POST /api/v1/financeiro/{id}/cancel/`
- `POST /api/v1/financeiro/generate-monthly-charges/`
- `GET|POST /api/v1/financeiro/subscriptions/`
- `POST /api/v1/financeiro/subscriptions/{id}/status/`

## Validação

```bash
cd backend && python manage.py migrate && pytest apps/financeiro/tests
cd ../frontend && npm run lint && npm run build
```
