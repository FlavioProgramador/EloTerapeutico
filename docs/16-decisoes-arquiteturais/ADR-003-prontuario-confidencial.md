# ADR-003 — Confidencialidade explícita no prontuário

## Status
Aceita.

## Data
10/07/2026.

## Contexto
Algumas evoluções não devem ser visíveis a todo usuário administrativo ou profissional com acesso geral ao paciente.

## Decisão
Evolução pode ser marcada confidencial. Apenas autor ou usuário/grupo com permissão explícita acessa; superusuário não recebe bypass na função dedicada. Exportação usa permissão separada.

## Alternativas consideradas
Motivação inferida. Alternativas: acesso por role global ou apenas pelo terapeuta responsável.

## Consequências positivas
- menor privilégio;
- separa administração de conteúdo clínico;
- exportação respeita solicitante;
- testes podem cobrir regra explícita.

## Consequências negativas
- gestão de permissões mais complexa;
- suporte/admin pode não visualizar para diagnóstico;
- todos os endpoints e exports precisam aplicar a regra.

## Riscos
Bypass em view legada, relatório ou admin. Exige inventário e testes contínuos.

## Referências no código
`apps/records/services/evolution_security.py`, models e testes confidenciais.

[Voltar](README.md)
