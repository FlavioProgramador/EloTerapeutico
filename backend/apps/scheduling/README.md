# Scheduling

O app `scheduling` é o pacote Python oficial do domínio de calendário e agendamentos do Elo Terapêutico. Ele concentra consultas, recorrências, bloqueios, disponibilidade, salas, pacotes, telemedicina, lembretes e integrações relacionadas.

## Pacote Python e app label

O contrato atual é:

```text
Pacote Python: apps.scheduling
App label Django: agenda
Nome visual: Agenda
```

O `SchedulingConfig` deve permanecer assim:

```python
class SchedulingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scheduling"
    label = "agenda"
    verbose_name = "Agenda"
```

O pacote legado `apps.agenda` foi removido. O label `agenda` continua intencionalmente porque preserva:

- tabelas `agenda_*`;
- migrations aplicadas;
- permissões `agenda.*`;
- ContentTypes;
- relações por string como `agenda.Appointment`;
- URLs do Django Admin em `/admin/agenda/`;
- identificadores persistidos por integrações.

Não altere o label para `scheduling` sem um projeto específico de migração de banco, permissões, ContentTypes e dados históricos.

## Entidades

O domínio gerencia:

- `Appointment`;
- `AppointmentRecurrence`;
- `ScheduleBlock`;
- `Room`;
- `PatientPackage`;
- `PackageSession`;
- `TelemedicineRoom`;
- `AppointmentReminder`.

## Estrutura

```text
scheduling/
├── admin/             # Django Admin separado por entidade
├── api/
│   └── v1/            # contratos HTTP oficiais
├── exceptions/        # erros controlados do domínio
├── integrations/      # fronteiras com outros módulos
├── migrations/        # histórico do app label agenda
├── models/            # persistência e invariantes locais
├── selectors/         # consultas sem efeitos colaterais
├── services/          # casos de uso e transações
└── tests/              # testes funcionais e arquiteturais
```

A direção de dependência é:

```text
URLs
  ↓
Views
  ↓
Serializers · Filters · Permissions
  ↓
Services · Selectors
  ↓
Models
```

Integrações externas seguem:

```text
View → Scheduling Service → Scheduling Integration → Outro domínio
```

## API

A única rota oficial é:

```text
/api/v1/scheduling/
```

A rota `/api/v1/agenda/` foi removida e deve retornar `404`.

Recursos disponíveis:

- `appointments/`;
- `appointment-recurrences/`;
- `schedule-blocks/`;
- `rooms/`;
- `patient-packages/`;
- `package-sessions/`;
- `telemedicine/`;
- `reminders/`;
- `telemedicine-access/<role>/<token>/`.

## Consultas e conflitos

Consultas reutilizáveis ficam em `selectors/`. A detecção de conflitos está centralizada em `selectors/conflicts.py` e considera:

- profissional;
- paciente e participantes;
- sala física;
- bloqueios de horário.

`Appointment.conflict_details()` continua disponível apenas como delegação ao selector canônico.

## Services e concorrência

Services controlam criação, atualização, mudança de status, recorrências, pacotes, telemedicina e lembretes. Operações concorrentes usam `transaction.atomic` e, quando necessário, `select_for_update`, especialmente em:

- criação e atualização de consultas;
- consumo e liberação de pacote;
- remoção de sessão;
- mudança de status;
- telemedicina;
- alterações de recorrência.

## Pacotes

O saldo nunca deve ficar negativo. Pacote, paciente, profissional e consulta devem pertencer ao mesmo escopo. Cancelamentos e remoções de sessão são casos de uso transacionais e não devem ser implementados em views.

## Telemedicina

Tokens de paciente e profissional são distintos, imprevisíveis e revogáveis. Eles não devem aparecer em logs nem ser exibidos no Django Admin. Views públicas validam papel, expiração e revogação antes de retornar dados da sessão.

## Financeiro

A fronteira com o app `financeiro` fica em `integrations/finance.py`. Scheduling informa o evento de negócio; regras financeiras permanecem no domínio financeiro.

A integração preserva:

- criação idempotente por consulta;
- cancelamento apenas de transação pendente;
- valor, profissional, paciente e vencimento;
- cobrança de pacote quando configurada.

## Comunicações

Imports Python devem usar `apps.scheduling`. Identificadores históricos persistidos, como `agenda.Appointment`, permanecem válidos porque utilizam o app label, não o nome do pacote Python.

O módulo técnico de signals usa `apps.communications.signals.scheduling`. O nome visual “Agenda” pode continuar na interface.

## Validação

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python apps/core/quality/check_backend_architecture.py
pytest apps/scheduling/tests -v
pytest --create-db
ruff check .
python manage.py spectacular --file schema.yml --validate
```

## Checklist antes de adicionar código

- O import usa `apps.scheduling`?
- A rota usa `/api/v1/scheduling/`?
- A operação é leitura ou alteração de estado?
- Uma leitura reutilizável está em selector?
- Uma alteração coordenada está em service?
- Todas as relações recebidas estão escopadas pelo ator?
- Existe risco de conflito de horário ou concorrência?
- Um pacote precisa ser bloqueado com `select_for_update`?
- A operação afeta financeiro ou comunicações?
- A view está acessando ORM ou alterando model diretamente?
- O app label `agenda` e as tabelas históricas foram preservados?
- Existem testes entre dois profissionais diferentes?
