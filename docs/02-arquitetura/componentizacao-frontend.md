# Componentização do frontend

## Objetivo

Esta referência descreve a organização adotada no frontend após a refatoração dos fluxos mais extensos. A divisão é baseada em responsabilidade e não apenas em quantidade de linhas.

A fonte de verdade continua sendo o código. Componentes visuais não devem assumir responsabilidades de autenticação, autorização, tenant, persistência remota ou montagem de contratos HTTP.

## Auditoria realizada

| Arquivo original | Tamanho aproximado | Situação | Decisão |
| --- | ---: | --- | --- |
| `features/records/components/evolution-editor-modal.tsx` | 854 linhas | estado, foco, queries, validação, templates, anexos e JSX juntos | dividido em componente de composição, controller, tipos, utilitários e três seções |
| `features/billing/checkout-wizard.tsx` | 761 linhas | planos, autenticação, idempotência, payload e três etapas juntos | dividido em controller, hooks de seleção/dados, regras puras e componentes por etapa |
| `features/agenda/components/appointment-modal.tsx` | 530 linhas | consultas, disponibilidade, payload e formulário juntos | dividido em hook, tipos, utilitários e quatro seções |
| `features/patients/components/patient-browser.tsx` | cerca de 300 linhas | implementação anterior | não é a rota atual; a página usa `PatientBrowserReference` |
| `features/records/components/record-workspace.tsx` | cerca de 285 linhas | composição de abas e estado local | mantido; já delega o conteúdo para componentes especializados |
| `features/agenda/components/agenda-workspace.tsx` | cerca de 206 linhas | composição do calendário e modais | mantido; tamanho compatível com a responsabilidade |

Arquivos legados de pacientes não foram removidos neste PR porque a exclusão exige uma verificação separada de consumidores, testes e histórico de rotas.

## Estrutura por feature

A estrutura não é obrigatória em todos os módulos, mas serve como referência:

```text
src/features/<feature>/
├── components/
│   ├── <fluxo-principal>.tsx
│   ├── <fluxo>/
│   │   ├── <secao>.tsx
│   │   ├── <tipos>.ts
│   │   └── <utilitarios>.ts
├── hooks/
├── services/
├── schemas/
├── types.ts
└── constants.ts
```

### Componente de composição

O componente principal organiza a tela, modal ou wizard. Ele pode:

- selecionar qual seção renderizar;
- fornecer callbacks e estado já preparados;
- aplicar layout e semântica;
- controlar abertura e fechamento.

Ele não deve:

- chamar `fetch`, Axios ou services diretamente;
- montar payloads complexos;
- concentrar validação de domínio;
- decidir autorização;
- persistir tokens ou dados clínicos no navegador.

### Controller ou hook de fluxo

Controllers locais coordenam estado e comportamento de uma tela complexa. Exemplos atuais:

- `useAppointmentForm`;
- `useEvolutionEditorController`;
- `useCheckoutWizard`.

Um controller pode consumir hooks de query e mutation, mas não substitui services. Quando crescer, deve delegar regras puras, seleção e formatação a arquivos menores.

### Componentes de seção

Seções recebem contratos explícitos e cuidam somente da interface de uma parte do fluxo. Elas não fazem chamadas HTTP e não conhecem detalhes de cookies, tokens ou endpoints.

## Componentes locais e compartilhados

Um componente permanece dentro da feature quando:

- usa tipos específicos do domínio;
- aparece em apenas um fluxo;
- contém linguagem clínica, financeira ou operacional específica;
- depende de regras particulares do módulo.

Um componente pode ir para `src/components` quando:

- é utilizado por mais de uma feature;
- possui contrato estável e neutro;
- não depende de services ou tipos de domínio;
- reduz duplicação real.

Não devem ser criados componentes globais excessivamente configuráveis apenas para reduzir linhas.

## Estado remoto e estado de interface

- TanStack Query mantém dados remotos, cache e invalidação;
- estado local mantém etapa ativa, modal aberto, campos ainda não enviados e feedback temporário;
- resultados de query não devem ser copiados para estado sem uma necessidade de edição;
- mutations invalidam apenas as chaves afetadas;
- components visuais não chamam services diretamente.

A troca futura de clínica deve continuar limpando ou segmentando caches conforme o contexto implementado. O backend permanece a autoridade para pertencimento e permissões.

## Server e Client Components

Use `"use client"` somente quando o arquivo precisar de:

- hooks React;
- eventos do navegador;
- contexto client-side;
- TanStack Query;
- APIs como clipboard, focus ou `window`.

Rotas e layouts que apenas compõem conteúdo devem permanecer Server Components quando possível. Extrair uma seção não é motivo suficiente para transformá-la em Client Component; ela herda a fronteira do importador quando não utiliza recursos client-side diretamente.

## BFF, sessão e API

O cliente HTTP usa `/api/backend/` e nunca adiciona `Authorization` vindo do navegador. O BFF mantém os tokens em cookies HttpOnly, adiciona autenticação no servidor e preserva proteção CSRF para métodos inseguros.

Regras obrigatórias:

- não usar `localStorage` ou `sessionStorage` para tokens;
- não construir chamadas paralelas fora do cliente HTTP existente;
- não usar role da interface como autorização definitiva;
- não expor IDs ou dados adicionais para facilitar componentes;
- não enviar dados clínicos ao gateway de pagamento.

## Formulários e modais

Formulários grandes devem manter uma única fonte de verdade e ser divididos por seções coesas. A submissão e a montagem de payload ficam no controller ou em utilitário puro.

Modais devem preservar:

- `role="dialog"` e `aria-modal`;
- foco inicial;
- focus trap quando implementado;
- retorno de foco;
- fechamento por teclado;
- confirmação de descarte;
- bloqueio durante submissão.

## Estados de carregamento, erro e vazio

Cada fluxo deve representar explicitamente:

- carregamento inicial;
- falha recuperável;
- ausência de dados;
- submissão em andamento;
- sucesso;
- falha parcial.

No checkout, falha ao carregar planos oferece nova tentativa. No editor clínico, falha parcial de anexos mantém a evolução salva e conserva apenas os arquivos pendentes.

## Testes

Priorize testes de comportamento e fronteiras arquiteturais. O arquivo `frontend-componentization.test.mjs` verifica que:

- componentes principais permanecem pequenos e orientados à composição;
- chamadas remotas ficam nos controllers;
- regras de confidencialidade, anexos e idempotência não foram removidas;
- as seções essenciais continuam presentes.

Comandos obrigatórios:

```bash
npm ci
npm run lint
npm run typecheck
npm test
npm run test:auth
npm run build
```

## Exemplos atuais

### Agenda

```text
AppointmentModal
→ useAppointmentForm
→ AppointmentWhoWhenSection
→ AppointmentDetailsSection
→ AppointmentOptionsSection
→ AppointmentAdministrativeSection
```

### Prontuário

```text
EvolutionEditor
→ useEvolutionEditorController
→ EvolutionLinkSection
→ EvolutionContentSection
→ EvolutionSecuritySection
```

### Checkout

```text
CheckoutWizard
→ useCheckoutWizard
→ CheckoutCustomerStep
→ CheckoutReviewStep
→ CheckoutSuccessStep
→ CheckoutPlanSummary
```

## Riscos e próximas etapas

- `useEvolutionEditorController` permanece extenso por coordenar salvamento e uploads sequenciais; uma próxima etapa pode extrair a persistência de anexos para um hook específico;
- componentes legados de pacientes devem ser removidos somente após confirmação de ausência de consumidores;
- dashboard, relatórios e formulários devem ser auditados novamente quando receberem novas funcionalidades;
- snapshots visuais ou testes end-to-end ainda são recomendados para detectar regressões de layout.

[Voltar](README.md)
