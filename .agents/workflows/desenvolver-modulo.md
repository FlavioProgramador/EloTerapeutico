---
description: Implementa uma entrega aprovada de um módulo usando agentes especializados.
---
Quando o usuário executar `/desenvolver-modulo <modulo>`:
1. Leia `.agents/agents.md` e atue como `@coordinator`.
2. Localize `docs/modules/<modulo>-spec.md` e confirme aprovação.
3. Se não houver especificação aprovada, execute o planejamento e pare.
4. Selecione somente a próxima entrega não concluída.
5. Delegue banco a `@database` com `migrations-seguras`, backend a `@backend` com `implementar-backend`, frontend a `@frontend` com `implementar-frontend`, testes a `@qa` com `testar-modulo`, navegador a `@qa` com `validar-navegador` e autorização a `@security` com `auditar-autorizacao`.
6. Não permita edição concorrente no mesmo arquivo.
7. Implemente uma entrega vertical, valide, documente e use `preparar-pull-request`.
8. Apresente o relatório e pare; não avance sem aprovação.
