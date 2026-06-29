---
name: migrations-seguras
description: Planeja e valida alterações em modelos, tabelas, índices, constraints e dados persistidos.
---
# Migrations seguras
1. Leia `.agents/agents.md` e atue como `@database`.
2. Inspecione schema e migrations existentes.
3. Classifique a mudança como aditiva, compatível, potencialmente destrutiva ou destrutiva.
4. Prefira coluna opcional, backfill separado e constraint posterior.
5. Gere e revise a migration; teste em banco local descartável.
6. Documente impacto, locks, rollback, backfill e compatibilidade.
7. Pare e peça aprovação para qualquer operação destrutiva.
8. Nunca apague dados automaticamente, use dados reais ou float para dinheiro.
