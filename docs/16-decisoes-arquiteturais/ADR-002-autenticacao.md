# ADR-002 — Autenticação JWT com rotação e blacklist

## Status
Aceita, com revisão pendente do armazenamento no frontend.

## Data
10/07/2026.

## Contexto
Frontend separado precisa autenticar chamadas à API e renovar sessões.

## Decisão
Usar Simple JWT com access curto, refresh mais longo, rotação, blacklist e claim ligado ao hash da senha.

## Alternativas consideradas
Motivação inferida. Alternativas: sessão Django, BFF com cookies HttpOnly ou provedor OIDC.

## Consequências positivas
- API stateless para access;
- revogação de refresh;
- invalidação após senha;
- cliente coordena renovação.

## Consequências negativas
- gestão de tokens no navegador;
- logout depende de blacklist;
- mais complexidade de refresh concorrente;
- mudança de signing key encerra sessões.

## Riscos
Cookies atuais são acessíveis ao JavaScript. A decisão de transporte/armazenamento deve ser revisada antes de produção clínica.

## Referências no código
`settings/base.py`, `apps/users/api/serializers.py`, `frontend/src/lib/api.ts`.

[Voltar](README.md)
