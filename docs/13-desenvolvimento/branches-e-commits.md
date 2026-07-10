# Branches e commits

## Branches

Formato:

```text
<tipo>/<descricao-em-kebab-case>
```

Exemplos:

- `feat/lembretes-agenda`;
- `fix/isolamento-documentos`;
- `security/cookies-autenticacao`;
- `docs/refatoracao-completa`.

Mantenha a branch focada. Atualize com `main` sem reescrever histórico compartilhado indevidamente.

## Commits

Formato recomendado:

```text
<tipo>(<escopo>): descricao objetiva em portugues
```

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `security`, `chore`, `ci`.

Exemplos:

```text
feat(agenda): adiciona validacao de conflito de sala
fix(records): restringe download confidencial ao autor
docs(api): documenta endpoint de exportacao
security(auth): move refresh para cookie httpOnly
```

## Regras

- um objetivo coerente por commit;
- não usar “ajustes” como descrição genérica;
- não misturar formatação massiva com regra de negócio;
- não incluir artefatos, `.env`, bancos ou uploads;
- migrations no mesmo conjunto da mudança de model;
- commits de documentação separados por assunto quando extensos.

[Voltar](README.md)
