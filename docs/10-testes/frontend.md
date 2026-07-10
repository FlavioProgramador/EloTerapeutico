# Testes frontend

## Checks disponíveis

```bash
npm run lint
npm run typecheck
npm test
npm run test:coverage
npm run build
```

O teste automatizado configurado no package usa o test runner do Node para `agenda-calendar.test.mjs`. O script de cobertura aplica limites altos especificamente a arquivos de calendário.

## Workflow

`frontend-ci.yml` usa Node 24, `npm ci`, ESLint, TypeScript sem emissão e build Next.js. Relatórios são anexados ao workflow.

## Lacunas

Não foi localizada uma stack abrangente de testes React para todos os módulos. Prioridades:

- AuthProvider e interceptores de refresh;
- guards e redirecionamentos;
- formulários de paciente/prontuário;
- estados loading/error/empty;
- checkout e erros 502;
- calendário e timezone;
- downloads/uploads;
- acessibilidade;
- E2E de login até operações críticas.

## Regras

Mockar API em testes de componente, mas manter testes de contrato separados. Não incluir tokens/dados reais em snapshots.

[Voltar](README.md)
