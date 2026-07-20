# API do backend

A API principal utiliza `/api/v1/`.

| Prefixo | Domínio |
| --- | --- |
| `/api/v1/auth/` | Autenticação |
| `/api/v1/patients/` | Pacientes |
| `/api/v1/records/` | Prontuário |
| `/api/v1/scheduling/` | Agenda e consultas |
| `/api/v1/finances/` | Financeiro clínico |
| `/api/v1/documents/` | Documentos |
| `/api/v1/reports/` | Relatórios |
| `/api/v1/forms/` | Formulários |
| `/api/v1/billing/` | Assinatura SaaS |
| `/api/v1/communications/` | Comunicações |

O nome visual “Financeiro” não cria uma rota `/financeiro/`. Consumidores devem utilizar `/api/v1/finances/`.

Endpoints protegidos exigem JWT. Recursos fora do escopo do usuário devem responder como inexistentes ou proibidos conforme o contrato, sem permitir enumeração.
