# Matriz de módulos

| Módulo | Backend | Frontend | API | Situação |
| --- | --- | --- | --- | --- |
| Autenticação | `apps/users` | login e cadastro | Sim | ✅ |
| Pacientes | `apps/patients` | `features/patients` | Sim | ✅ |
| Prontuário | `apps/records` | `features/records` | Sim | ✅ |
| Agenda | `apps/scheduling` (`label=agenda`) | `features/agenda` | `/api/v1/scheduling/` | ✅ |
| Financeiro | `apps/finances` (`label=financeiro`) | `features/financeiro` | `/api/v1/finances/` | ✅ |
| Billing | `apps/billing` | checkout/assinatura | `/api/v1/billing/` | ✅ |
