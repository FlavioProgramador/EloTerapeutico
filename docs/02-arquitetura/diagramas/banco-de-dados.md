# Diagrama resumido de dados

```mermaid
erDiagram
    USER ||--o{ PATIENT : responsavel
    USER ||--o{ APPOINTMENT : atende
    PATIENT ||--o{ APPOINTMENT : possui
    PATIENT ||--o{ EVOLUTION : possui
    APPOINTMENT o|--o| EVOLUTION : origina
    EVOLUTION ||--o{ EVOLUTION_ADDENDUM : recebe
    PATIENT ||--o{ CLINICAL_DOCUMENT : possui
    PATIENT ||--o{ CLINICAL_EXPORT : exporta
    USER ||--o{ FINANCIAL_TRANSACTION : registra
    PATIENT o|--o{ FINANCIAL_TRANSACTION : referencia
    USER ||--o{ DOCUMENT_TEMPLATE : possui
    DOCUMENT_TEMPLATE o|--o{ GENERATED_DOCUMENT : gera
    PATIENT ||--o{ GENERATED_DOCUMENT : recebe
    USER ||--o{ SUBSCRIPTION : assina
    PLAN ||--o{ SUBSCRIPTION : define
    SUBSCRIPTION ||--o{ PAYMENT : cobra
    USER ||--o{ AUDIT_LOG : executa
```

O diagrama omite campos e entidades auxiliares para legibilidade. As migrations e models são a fonte de verdade.

[Anterior](containers.md) · [Próximo: sequências](sequencias.md) · [Voltar](../README.md)
