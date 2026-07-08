# Agenda

## Visão geral

O módulo reúne calendário, consultas, bloqueios, recorrências, pacotes de sessões, lembretes e atendimento online. Ele reutiliza pacientes e profissionais existentes e mantém o isolamento por profissional no backend.

## Frontend

- `/dashboard/agenda`: calendário diário, semanal e mensal;
- `/dashboard/agenda/recurrences`: séries recorrentes;
- `/dashboard/agenda/packages`: pacotes de sessões;
- `/dashboard/agenda/atendimento-online`: consultas online;
- `/consulta-online/{role}/{token}`: validação de acesso temporário.

A data e a visualização são refletidas em `date` e `view` na URL. A última visualização também é salva no navegador.

## Domínio

`Appointment` representa a consulta. `AppointmentRecurrence` guarda a regra de repetição. `ScheduleBlock` registra indisponibilidade sem cancelar consultas. `Room` representa sala física. `PatientPackage` e `PackageSession` controlam saldo e histórico. `TelemedicineRoom` mantém tokens independentes e revogáveis. `AppointmentReminder` funciona como fila persistida de lembretes administrativos.

## Conflitos

A API verifica interseção de intervalos para profissional, paciente, participantes de grupo, sala e bloqueios ativos. Séries e pacotes são materializados dentro de transações.

## Segurança

- isolamento por `therapist_id` para terapeutas;
- autorização de objeto no backend;
- tokens UUID temporários para acesso online;
- destinatários de lembretes mascarados;
- sem conteúdo clínico nas observações da agenda;
- auditoria de criação, atualização, exportação e acesso online.

## Endpoints

Os recursos ficam sob `/api/v1/agenda/`:

- `appointments/`;
- `appointment-recurrences/`;
- `schedule-blocks/`;
- `rooms/`;
- `patient-packages/`;
- `package-sessions/`;
- `telemedicine/`;
- `reminders/`;
- `telemedicine-access/{role}/{token}/`.

Consultas oferecem ações de confirmar, cancelar, concluir, registrar falta, remarcar, verificar disponibilidade e exportar. Recorrências oferecem pausa, reativação, encerramento e alteração por escopo.

## Validação

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest apps/agenda/tests/test_agenda_complete.py -q

cd ../frontend
npm run test:agenda
npm run lint
npx tsc --noEmit
npm run build
```

A integração real de vídeo e o envio real de WhatsApp permanecem desacoplados e dependem de provedores externos e workers.
