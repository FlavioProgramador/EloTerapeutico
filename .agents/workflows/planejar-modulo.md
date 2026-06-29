---
description: Analisa um módulo e cria uma especificação técnica antes de qualquer implementação.
---
Quando o usuário executar `/planejar-modulo <modulo>`:
1. Leia `.agents/agents.md` e atue como `@coordinator`.
2. Acione `@architect` com a skill `planejar-modulo`.
3. Crie ou atualize `docs/modules/<modulo>-spec.md`.
4. Apresente resumo, escopo, dependências, arquivos previstos, divisão em PRs, riscos e critérios de aceite.
5. Não altere código de produção.
6. Pare e aguarde o usuário escrever `Aprovado`.
