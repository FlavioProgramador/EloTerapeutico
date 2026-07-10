# Endpoints — Pacientes

Base: `/api/v1/patients/`.

| Método | Sufixo | Descrição |
| --- | --- | --- |
| GET | `` | Lista filtrada e paginada |
| POST | `` | Cria paciente |
| GET/PATCH/PUT/DELETE | `{id}/` | Operações padrão autorizadas |
| POST | `{id}/deactivate/` | Desativa conforme lifecycle |
| POST | `{id}/restore/` | Restaura incluindo arquivados no queryset |
| GET | `{id}/form/` | Contrato de formulário + detalhe |
| GET | `{id}/dashboard/` | Workspace e indicadores |
| GET | `dashboard-metrics/` | Métricas agregadas |
| POST | `import-csv/` | Preview/importação confirmada |
| GET | `export-csv/` | CSV filtrado com CPF mascarado |
| GET/POST | `{id}/reminders/` | Lembretes do paciente |

## Filtros e escopo

O ViewSet usa `patients_accessible_to`. A listagem aplica serializer reduzido; create/update usa serializer de formulário; detalhe usa serializer completo autorizado.

## Importação CSV

- multipart com campo `file`;
- `confirm=false` para preview;
- máximo 2 MB e 500 registros;
- UTF-8;
- colunas obrigatórias `full_name`, `cpf`, `birth_date`;
- somente terapeuta;
- confirmação só ocorre sem erros/duplicidades.

## Segurança

Secretária não deve atualizar objeto pelo permission principal. Exportações são auditadas. Campos e actions adicionais de convite/formulário devem ser consultados no schema atual.

[Voltar à API](../README.md)
