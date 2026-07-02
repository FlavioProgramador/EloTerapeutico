# AGENTS.md — Elo Terapêutico

## Produto

O Elo Terapêutico é uma plataforma de gestão para terapeutas. Os módulos podem incluir landing page, autenticação, pacientes, agenda, sessões, prontuários, financeiro, relatórios, configurações e recursos assistivos de IA.

## Regra principal

Antes de editar, analise o código existente. Não presuma framework, estrutura de pastas ou contrato que não esteja presente no repositório.

## Segurança e privacidade

- Nunca use dados reais de pacientes em código, testes, screenshots, documentação ou logs.
- Todo recurso de domínio deve ser isolado pelo terapeuta autenticado no backend.
- Ocultar um botão no frontend não é autorização.
- Não registre prontuários, tokens, senhas ou informações sensíveis em logs.
- Não adicione segredos ao Git.
- Não desative validações de segurança para fazer uma funcionalidade funcionar.
- Não execute migrations destrutivas, deploy ou alterações em produção.

## Engenharia

- Preserve a stack e os padrões existentes.
- Prefira mudanças pequenas, revisáveis e compatíveis.
- Não instale dependências sem justificar.
- Evite duplicação, arquivos monolíticos e acoplamento desnecessário.
- Documente mudanças de contratos compartilhados.
- Use transações para operações críticas.
- Evite consultas N+1 e carregamento excessivo de dados.

## Frontend

- Produza uma interface profissional, humana e apropriada para saúde e bem-estar.
- Evite aparência genérica de template produzido por IA.
- Implemente loading, erro, vazio e sucesso.
- Garanta responsividade e acessibilidade básica.
- Use animações apenas quando ajudarem na compreensão.

## IA no produto

- IA pode auxiliar com organização e rascunhos revisáveis.
- IA não deve realizar diagnóstico, prescrição ou decisão clínica autônoma.
- Toda saída sensível deve ser revisada pelo terapeuta.

## Validação

Ao concluir uma tarefa:

1. Rode lint e formatter existentes.
2. Rode typecheck quando aplicável.
3. Rode testes relevantes.
4. Rode build quando viável.
5. Verifique migrations.
6. Revise o diff.
7. Informe arquivos alterados, comandos executados, resultados e riscos restantes.
