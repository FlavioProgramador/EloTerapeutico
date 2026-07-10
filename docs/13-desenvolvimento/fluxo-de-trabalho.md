# Fluxo de trabalho

## 1. Preparar

```bash
git checkout main
git pull --ff-only
git checkout -b feat/nome-curto
```

Use `fix/`, `feat/`, `docs/`, `refactor/`, `test/`, `security/` ou `chore/` conforme o objetivo.

## 2. Analisar

- leia `AGENTS.md`;
- identifique models, serializers, views, services, permissions e testes;
- confirme frontend e contratos de API;
- verifique migrations e configuração;
- defina riscos de segurança/LGPD.

## 3. Implementar

- preserve compatibilidade quando necessária;
- mantenha regra no domínio/backend;
- use selectors para escopo;
- valide no serializer e constraint quando apropriado;
- trate estados loading/error/empty no frontend;
- não use mocks em código de produção.

## 4. Testar

Execute checks focados durante o desenvolvimento e a suíte relevante antes do PR.

## 5. Documentar

Atualize módulo, API, caso de uso, segurança, variáveis e ADR quando a mudança afetar esses temas.

## 6. Publicar

- revise `git diff`;
- crie commits pequenos;
- faça push da branch;
- abra Pull Request em rascunho;
- aguarde CI e revisão;
- não faça merge automático sem processo aprovado.

[Voltar](README.md)
