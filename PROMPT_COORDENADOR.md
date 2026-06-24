# Prompt coordenador dos agentes

Use este prompt em uma thread principal do Codex App ou CLI:

```text
Leia o AGENTS.md e a configuração em .codex/agents.

Quero organizar o trabalho do Elo Terapêutico com agentes especializados.

Primeiro, não implemente nada. Faça o seguinte:
1. Peça ao agente seguranca uma auditoria somente leitura.
2. Peça aos agentes landing_page, agenda, pacientes_prontuarios, financeiro,
   autenticacao_permissoes, testes_qa e documentacao_docker que analisem apenas
   sua área e produzam um plano curto.
3. Espere todos concluírem.
4. Consolide os resultados, identifique dependências, arquivos compartilhados
   e riscos de conflito.
5. Proponha uma ordem de execução em ondas e um PR separado por módulo.
6. Não permita que dois agentes editem simultaneamente o mesmo arquivo
   compartilhado.
7. Não faça deploy, não use dados reais e não execute migrations destrutivas.

No resumo, apresente:
- diagnóstico de cada agente;
- dependências entre módulos;
- contratos que precisam ser definidos primeiro;
- ordem dos worktrees;
- branches sugeridas;
- critérios de aceite de cada PR.
```

## Execução recomendada por ondas

### Onda 1 — baixo conflito

- `landing_page`
- `autenticacao_permissoes`
- `seguranca` em somente leitura
- `documentacao_docker`

### Onda 2 — módulos dependentes dos contratos de identidade

- `agenda`
- `pacientes_prontuarios`
- `financeiro`

### Onda 3 — validação integrada

- `testes_qa`
- nova revisão do `seguranca`

## Branches sugeridas

- `feat/landing-page`
- `feat/agenda`
- `feat/pacientes-prontuarios`
- `feat/financeiro`
- `feat/autenticacao-permissoes`
- `test/quality-suite`
- `audit/security-review`
- `chore/docs-docker`

Cada implementação deve ser iniciada em um Worktree separado baseado na mesma
branch estável, normalmente `main` ou `develop`.
