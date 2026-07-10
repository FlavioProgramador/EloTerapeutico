# Códigos e estados de domínio

## Consulta

`scheduled`, `confirmed`, `completed`, `missed`, `cancelled`, `rescheduled`.

## Paciente

`active`, `evaluation`, `waiting_return`, `discharged`, `inactive`, `archived`.

## Transação financeira

`paid`, `partial`, `pending`, `cancelled`, `refunded`.

## Documento gerado

`draft`, `processing`, `completed`, `failed`, `cancelled`, `archived`.

## Formulário

`active`, `archived`.

## Submissão de formulário

`draft`, `submitted`, `reviewed`, `archived`.

## Exportação clínica

`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `EXPIRED`.

## Assinatura SaaS

`TRIALING`, `PENDING`, `ACTIVE`, `PAST_DUE`, `CANCELED`, `EXPIRED`.

## Pagamento SaaS

`PENDING`, `CONFIRMED`, `RECEIVED`, `OVERDUE`, `REFUNDED`, `CANCELED`, `FAILED`.

A fonte de verdade são os `TextChoices` do commit executado.

[Voltar](README.md)
