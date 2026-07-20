# Apps e responsabilidades

| App | Responsabilidade |
| --- | --- |
| `core` | Infraestrutura e qualidade compartilhada |
| `users` | Autenticação e usuários |
| `patients` | Pacientes |
| `records` | Prontuário |
| `scheduling` (`label=agenda`) | Agenda, consultas e pacotes |
| `finances` (`label=financeiro`) | Receitas, despesas, pagamentos e mensalidades clínicas |
| `documents` | Documentos e PDFs |
| `reports` | Indicadores e exportações |
| `forms` | Formulários |
| `billing` | Planos e assinatura SaaS |
| `communications` | Notificações e automações |
| `audit` | Auditoria |

## Fronteira financeira

`apps.finances` é o livro operacional do profissional. `apps.billing` é a operação comercial do SaaS Elo Terapêutico. Os módulos não compartilham models nem gateways por conveniência.

## Dependências

Integrações entre domínios são explícitas. Scheduling delega criação/cancelamento de lançamentos aos services públicos de `finances`; communications consome selectors e eventos sem duplicar regras financeiras.
