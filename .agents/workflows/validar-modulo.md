---
description: Executa QA, navegador e revisão de autorização de um módulo implementado.
---
Quando o usuário executar `/validar-modulo <modulo>`:
1. Leia `.agents/agents.md` e a especificação do módulo.
2. Atue como `@coordinator`.
3. Acione `@qa` com `testar-modulo` e `validar-navegador`.
4. Acione `@security` em somente leitura com `auditar-autorizacao`.
5. Execute lint, typecheck, testes e build existentes.
6. Compare com os critérios de aceite.
7. Produza resultados, falhas, evidências, riscos, bloqueadores e recomendação de aprovação ou rejeição.
