# Endpoints — Agenda

Base canônica: `/api/v1/scheduling/`. O prefixo `/api/v1/agenda/` permanece como alias temporário de compatibilidade.

Routers:

- `appointments/`;
- `appointment-recurrences/`;
- `schedule-blocks/`;
- `rooms/`;
- `patient-packages/`;
- `package-sessions/`;
- `telemedicine/`;
- `reminders/`.

Acesso público específico:

- `telemedicine-access/{role}/{uuid:token}/`.

## Payload mínimo conceitual de consulta

```json
{
  "patient": 101,
  "start_time": "2026-07-15T13:00:00-03:00",
  "end_time": "2026-07-15T13:50:00-03:00",
  "modality": "online",
  "appointment_type": "psychotherapy",
  "session_value": "150.00"
}
```

## Validações

- intervalo positivo;
- ausência de conflito;
- sala ativa e compatível;
- valor não negativo;
- participantes acessíveis;
- recorrência válida.

Actions de confirmação, conclusão, cancelamento, remarcação, recorrência e telemedicina são declaradas nos ViewSets; gere o schema para nomes e payloads exatos.

[Voltar à API](../README.md)
