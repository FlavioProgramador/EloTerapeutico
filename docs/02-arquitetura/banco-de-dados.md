# Banco de dados

## Tecnologias

- PostgreSQL 15 no Docker Compose;
- `DATABASE_URL` interpretada pelo django-environ;
- SQLite como fallback no desenvolvimento e banco determinístico nos testes.

## Grupos de dados

| Domínio | Entidades principais |
| --- | --- |
| Usuários | `User`, `WorkingHours` |
| Pacientes | `Patient`, `PatientProfessional`, `PatientRegistrationInvite` |
| Prontuário | `Anamnesis`, `Evolution`, `EvolutionAddendum`, `ClinicalDocument`, `ClinicalExport`, `TreatmentGoal` |
| Agenda | `Appointment`, `AppointmentRecurrence`, `ScheduleBlock`, `Room`, `TelemedicineRoom`, pacotes e lembretes |
| Financeiro | `FinancialTransaction`, `MonthlySubscription` |
| Documentos | `DocumentTemplate`, `GeneratedDocument`, `DocumentSequence` |
| Formulários | `FormTemplate`, `TherapeuticForm`, `FormField`, `FormSubmission`, `FormAnswer` |
| Billing | `Plan`, `Subscription`, `Payment`, `WebhookEvent`, `FeatureUsage` |
| Auditoria | `AuditLog` |

## Integridade

O código usa:

- `PROTECT` em vínculos clínicos e documentais que não devem desaparecer em cascata;
- constraints para datas, valores e unicidade;
- indexes por proprietário, status, data e referências externas;
- soft delete/arquivamento em alguns domínios;
- versões e snapshots para preservar histórico;
- criptografia em campos textuais selecionados, não no banco inteiro.

## Migrations

Migrations são a fonte de verdade do schema. Antes de qualquer deploy:

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate
```

Não gere migrations manualmente em produção. Faça backup e valide rollback antes de alterações destrutivas.

## Multi-tenancy

Não existe coluna ou entidade tenant comum a todos os modelos. Chaves para usuário/terapeuta fornecem isolamento parcial, mas não substituem um desenho multi-tenant completo.

[Voltar](README.md)
