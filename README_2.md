# Agentes Codex — Elo Terapêutico

Este pacote contém oito agentes personalizados, um arquivo de configuração,
instruções globais do projeto e um prompt coordenador.

## Estrutura

```text
.codex/
├── config.toml
└── agents/
    ├── landing-page.toml
    ├── agenda.toml
    ├── pacientes-prontuarios.toml
    ├── financeiro.toml
    ├── autenticacao-permissoes.toml
    ├── testes-qa.toml
    ├── seguranca.toml
    └── documentacao-docker.toml
AGENTS.example.md
OWNERSHIP.md
PROMPT_COORDENADOR.md
```

## Instalação no projeto

1. Extraia o pacote na raiz do repositório.
2. Renomeie `AGENTS.example.md` para `AGENTS.md`.
3. Revise o `AGENTS.md` para refletir a stack real.
4. Mantenha `.codex/agents/` versionado no Git.
5. Abra uma nova sessão do Codex para que as instruções sejam carregadas.
6. Use o prompt de `PROMPT_COORDENADOR.md`.

## Uso como agentes personalizados

Os arquivos TOML definem agentes do projeto. Cada agente herda o modelo da
sessão principal e possui escopo, sandbox e instruções próprias.

Exemplo de prompt:

```text
Use o agente agenda para analisar o módulo atual, propor um plano e implementar
somente a correção de conflitos de horário. Rode os testes relevantes e
apresente o diff final.
```

## Uso com Worktrees

Para mudanças paralelas, crie uma thread Worktree separada para cada módulo.
Não coloque dois agentes de escrita na mesma worktree. Use o agente `seguranca`
em modo somente leitura para revisar as branches.

## Observações

- `seguranca` está configurado com `sandbox_mode = "read-only"`.
- Os demais agentes usam `workspace-write`.
- `max_threads = 8` permite até oito threads abertas, mas o consumo de recursos
  e tokens aumenta. Reduza para 4 ou 6 se o computador ficar lento.
- Os modelos não foram fixados nos arquivos, permitindo herdar o modelo
  selecionado na sessão principal.
