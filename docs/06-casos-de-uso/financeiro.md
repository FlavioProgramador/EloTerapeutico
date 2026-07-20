# Casos de uso — Financeiro

## Registrar transação

O profissional registra receita ou despesa no próprio escopo. Paciente e consulta, quando informados, devem pertencer ao mesmo terapeuta.

## Registrar pagamento

Pagamentos podem ser parciais ou integrais. O backend bloqueia valor maior que o saldo e transações incompatíveis com pagamento.

## Cancelar ou estornar

Cancelamento é permitido em pendente/parcial; estorno somente em pago. As ações preservam o histórico.

## Mensalidades

A criação da mensalidade e da primeira cobrança ocorre na mesma transação de banco.

## Cobrança por consulta

A geração em lote é idempotente e preserva o contrato `created`, `skipped` e `created_count`.
