# ADR-004 — Exportações assíncronas com fila no banco

## Status
Aceita.

## Data
10/07/2026.

## Contexto
Gerar PDF clínico pode exceder o tempo de uma requisição e precisa de retries e rastreabilidade.

## Decisão
Persistir jobs em `ClinicalExport` e processar com `run_export_worker`, usando locks do banco e estados explícitos.

## Alternativas consideradas
Motivação inferida. Alternativas: thread na requisição, Celery/Redis, serviço de filas gerenciado.

## Consequências positivas
- não depende de broker adicional;
- job e estado são transacionais;
- múltiplos workers usam `skip_locked`;
- retry e recuperação de job preso.

## Consequências negativas
- polling do banco;
- worker separado obrigatório;
- escalabilidade limitada comparada a broker;
- observabilidade precisa ser construída.

## Riscos
Worker parado, job antigo, PDF parcial e storage indisponível. SQLite não representa concorrência de produção.

## Referências no código
`apps/records/treatment_models.py`, `management/commands/run_export_worker.py`.

[Voltar](README.md)
