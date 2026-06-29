---
name: implementar-backend
description: Implementa APIs e regras de negócio aprovadas do Elo Terapêutico.
---
# Implementar backend
1. Leia `.agents/agents.md`, atue como `@backend` e leia a especificação aprovada.
2. Descubra os padrões reais e liste arquivos previstos.
3. Implemente regras em services testáveis e valide toda entrada no servidor.
4. Derive o terapeuta do usuário autenticado; não aceite troca de proprietário pelo payload.
5. Aplique filtro e autorização por objeto em todas as operações.
6. Use transações, paginação e consultas eficientes quando necessário.
7. Não registre conteúdo clínico em logs.
8. Teste autenticado, anônimo, outro terapeuta, ID inválido, payload inválido e regras de negócio.
9. Rode as verificações da stack e documente contratos de API.
