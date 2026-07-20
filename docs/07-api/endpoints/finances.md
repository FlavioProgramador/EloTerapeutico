# Endpoints — Financeiro

Base canônica: `/api/v1/finances/`.

## Operações

- CRUD de transações;
- `/{id}/pay/`;
- `/{id}/cancel/`;
- `/{id}/refund/`;
- `/pending/`;
- `/summary/`;
- `/export/`;
- `/subscriptions/`;
- `/subscriptions/{id}/status/`;
- `/unbilled-appointments/`;
- `/generate-monthly-charges/`.

O nome visual continua “Financeiro”, mas consumidores HTTP devem usar `finances`.
