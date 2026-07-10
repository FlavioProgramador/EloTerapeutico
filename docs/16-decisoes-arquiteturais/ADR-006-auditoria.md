# ADR-006 — Auditoria imutável e minimizada

## Status
Aceita.

## Data
10/07/2026.

## Contexto
Ações sobre dados sensíveis precisam de rastreabilidade sem duplicar prontuário em logs.

## Decisão
Usar `AuditLog` com ação, usuário, horário, IP, user agent e referência genérica. Impedir update/delete no model e registrar representação técnica mínima.

## Alternativas consideradas
Motivação inferida. Alternativas: event log externo, SIEM, CDC ou auditoria somente de infraestrutura.

## Consequências positivas
- trilha consultável no mesmo domínio;
- minimização de conteúdo;
- mixin reutilizável;
- IP de proxy controlado.

## Consequências negativas
- falha é fail-open;
- cobertura depende da instrumentação;
- administrador do banco pode alterar;
- banco cresce sem retenção.

## Riscos
Ação sensível sem log, log indisponível ou confiança incorreta em proxy. Produção pode exigir trilha externa append-only.

## Referências no código
`apps/audit/models.py`, `core/audit.py`.

[Voltar](README.md)
