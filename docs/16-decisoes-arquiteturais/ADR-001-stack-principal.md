# ADR-001 — Stack principal Django e Next.js

## Status
Aceita na implementação atual.

## Data
10/07/2026 — data de formalização documental.

## Contexto
O produto precisa de API, backoffice, modelagem relacional, interface rica e módulos clínicos/administrativos.

## Decisão
Usar Django/DRF no backend, Next.js/React no frontend e PostgreSQL como banco principal.

## Alternativas consideradas
Não há registro histórico suficiente. Motivação inferida a partir da implementação atual. Alternativas possíveis seriam monólito Django server-rendered ou API em outro framework.

## Consequências positivas
- ecossistema maduro;
- Django Admin/Unfold;
- ORM e migrations;
- frontend modular;
- separação de deploy e responsabilidades.

## Consequências negativas
- dois runtimes e pipelines;
- contratos precisam permanecer sincronizados;
- autenticação entre origens aumenta complexidade;
- duplicação possível de validações.

## Riscos
CORS, tokens no navegador, divergência de tipos e operação separada.

## Referências no código
`backend/requirements/base.txt`, `frontend/package.json`, `docker-compose.yml`.

[Voltar](README.md)
