# Diagrama de contexto

```mermaid
flowchart LR
    T[Terapeuta] --> E[Elo Terapêutico]
    S[Secretária] --> E
    A[Administrador] --> E
    E --> AS[Asaas]
    E --> SMTP[Servidor SMTP]
    E --> AZ[Azure Blob opcional]
```

- terapeuta: pacientes, agenda, prontuário, financeiro e recursos do plano;
- secretária: acesso administrativo limitado; não deve acessar prontuário clínico por padrão;
- administrador: backoffice e funções autorizadas, sem acesso automático a conteúdo confidencial;
- Asaas: processamento de billing;
- SMTP: redefinição de senha;
- Azure Blob: armazenamento privado quando configurado.

[Próximo: containers](containers.md) · [Voltar](../README.md)
