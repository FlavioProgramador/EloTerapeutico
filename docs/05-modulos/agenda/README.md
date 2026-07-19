# Módulo de agenda

**Status: implementado.**

## Finalidade

Gerenciar consultas, recorrências, bloqueios, salas, pacotes, sessões de pacote, lembretes e acesso de telemedicina.

## Entidades

- `Appointment`;
- `AppointmentRecurrence`;
- `ScheduleBlock`;
- `Room`;
- `PatientPackage` e `PackageSession`;
- `TelemedicineRoom`;
- `AppointmentReminder`.

## Consulta

Status: `scheduled`, `confirmed`, `completed`, `missed`, `cancelled`, `rescheduled`.

Modalidades: presencial, online e híbrida. Tipos incluem avaliação, psicoterapia, retorno, orientação, grupo e outro. Origem pode ser manual, recorrência, pacote ou remarcação.

## Regras de negócio

- término deve ser posterior ao início;
- valor da sessão não pode ser negativo;
- duração é recalculada no `save`;
- consultas ativas são agendadas ou confirmadas;
- conflito considera terapeuta, paciente/participantes, sala e bloqueios;
- consulta online não usa sala física;
- sala inativa não pode ser selecionada;
- recorrências suportam semanal, quinzenal e mensal;
- pagamento integral de transação vinculada pode confirmar consulta agendada;
- telemedicina usa tokens e rota pública específica por papel.

## API

Prefixo canônico `/api/v1/scheduling/` (com `/api/v1/agenda/` como alias temporário):

- `appointments/`;
- `appointment-recurrences/`;
- `schedule-blocks/`;
- `rooms/`;
- `patient-packages/`;
- `package-sessions/`;
- `telemedicine/`;
- `reminders/`;
- `telemedicine-access/{role}/{token}/`.

ViewSets possuem actions de operação, recorrência e telemedicina. Consulte o schema OpenAPI para métodos e payloads exatos.

## Frontend

`features/agenda` implementa calendário, modal de consulta e recorrências. A interface deve evitar criar conflito apenas visualmente; a API valida novamente.

## Permissões e segurança

Querysets devem ser filtrados pelo profissional acessível. Tokens de telemedicina são credenciais e não devem aparecer em logs. Notas do agendamento são administrativas e não devem substituir prontuário.

## Testes

Há testes completos de agenda, telemedicina, performance e teste frontend do calendário via Node test runner.

## Limitações

- infraestrutura de mídia da telemedicina não é comprovada pela presença dos modelos;
- envio efetivo de lembretes depende de canal/serviço operacional;
- timezones e horário de verão devem ser testados no ambiente final;
- concorrência deve ser validada em PostgreSQL, não apenas SQLite.

[Voltar aos módulos](../README.md)
