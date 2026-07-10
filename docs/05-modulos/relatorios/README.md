# Módulo de relatórios

**Status: implementado; cobertura e operação parcialmente documentadas.**

## Finalidade

Gerar visões agregadas para consultas, pacientes, financeiro e agendamento online, além de exportar resultados.

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/api/v1/reports/appointments/` | Relatório de consultas |
| GET | `/api/v1/reports/patients/` | Relatório de pacientes |
| GET | `/api/v1/reports/financial/` | Relatório financeiro |
| GET | `/api/v1/reports/online-scheduling/` | Agendamento online |
| GET/POST | `/api/v1/reports/export/` | Exportação conforme view |

Os parâmetros e formato exatos devem ser consultados no OpenAPI gerado pelo commit em execução.

## Frontend

`features/reports/reports-dashboard.tsx` apresenta filtros e resultados no dashboard.

## Regras e segurança

- consultas devem usar apenas dados acessíveis ao usuário;
- agregação não pode contornar confidencialidade;
- filtros de data precisam ter timezone coerente;
- exportações devem registrar auditoria quando contêm dados pessoais;
- CSV deve prevenir formula injection quando valores livres forem exportados;
- relatórios não são documentos contábeis ou clínicos oficiais sem validação.

## Limitações

Não foi localizada uma suíte isolada de testes do app `reports` equivalente às suítes de records/agenda/financeiro. Os relatórios dependem das regras e testes dos domínios fonte.

[Voltar aos módulos](../README.md)
