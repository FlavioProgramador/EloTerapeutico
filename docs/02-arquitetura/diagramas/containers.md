# Diagrama de containers

```mermaid
flowchart TB
    Browser[Navegador]
    Front[Container Next.js]
    API[Container Django]
    Worker[Container Worker]
    DB[(PostgreSQL)]
    Files[(Azure Blob ou filesystem)]
    Gateway[Asaas]

    Browser --> Front
    Front --> API
    API --> DB
    API --> Files
    API --> Gateway
    Worker --> DB
    Worker --> Files
```

No Docker Compose local, frontend, backend, banco e worker são serviços separados. Redis não faz parte do compose analisado; em produção ele é configurado como cache por `REDIS_URL`.

[Anterior](contexto.md) · [Próximo: banco](banco-de-dados.md) · [Voltar](../README.md)
