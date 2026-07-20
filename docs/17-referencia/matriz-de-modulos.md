# Matriz de módulos

| Módulo | Backend | Frontend | API | Testes encontrados | Situação |
| --- | --- | --- | --- | --- | --- |
| Autenticação | `apps/users` | login, cadastro e recuperação | Sim | Sim | ✅ |
| Usuários | `apps/users` | configurações/perfil | Sim | Sim | ✅ |
| Dashboard | agregações por domínio | `features/dashboard` | Indireta | Parcial | 🟡 |
| Pacientes | `apps/patients` | `features/patients` | Sim | Sim | ✅ |
| Prontuário | `apps/records` | `features/records` | Sim | Sim | ✅ |
| Agenda | `apps/scheduling` (`label=agenda`) | `features/agenda` | `/api/v1/scheduling/` | Sim | ✅ |
| Financeiro | `apps/financeiro` | `features/financeiro` | Sim | Sim | ✅ |
| Documentos | `apps/documents` | dashboard/documentos | Sim | Sim | ✅ |
| Formulários | `apps/forms` | dashboard/formularios | Sim | Sim | ✅ |
| Relatórios | `apps/reports` | `features/reports` | Sim | Testes não catalogados como suíte própria | 🟡 |
| Billing | `apps/billing` | checkout/assinatura | Sim | Sim | ✅ |
| Auditoria | `apps/audit`, `core/audit.py` | Backoffice | Sem API pública própria | Sim | ✅ |
| Administração | Django Admin/Unfold | Backoffice Django | Administração server-rendered | Parcial | ✅ |
| Tenant/clínica | Ausente | Ausente | Ausente | Ausente | 🔴 |
| IA clínica autônoma | Não comprovada | Não comprovada | Endpoint de status/resumo | Não conclusivo | 📌 |

A situação `✅` indica implementação verificada, não garantia de prontidão operacional.

[Voltar](README.md)
