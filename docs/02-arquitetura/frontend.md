# Frontend

## Stack

- Next.js 16.2.11 com App Router;
- React 19.2.4;
- TypeScript 6;
- Tailwind CSS 4;
- TanStack Query 5 para estado remoto;
- Axios para o cliente HTTP do BFF;
- React Hook Form e Zod nos formulários que adotam schema;
- Radix UI, Lucide e Framer Motion na interface.

## Organização

```text
frontend/src/
├── app/          # rotas, layouts e endpoints do BFF
├── components/   # componentes compartilhados e design system
├── contexts/     # estado global de interface e autenticação
├── features/     # módulos por domínio
├── lib/          # cliente HTTP, sessão client-side e utilitários
├── providers/    # providers raiz
└── types/        # contratos TypeScript compartilhados
```

As features concentram componentes, hooks, services, schemas, tipos e regras específicas do domínio. Fluxos extensos usam um componente de composição, um controller local e seções visuais coesas.

Consulte [Componentização do frontend](componentizacao-frontend.md) para critérios, auditoria e exemplos reais.

## Rotas verificadas

- landing page;
- login, cadastro e redefinição de senha;
- checkout e páginas de resultado de billing;
- dashboard;
- pacientes e workspace do paciente;
- prontuário;
- agenda e recorrências;
- financeiro;
- documentos;
- formulários;
- relatórios;
- assinatura e faturas;
- configurações.

## Cliente HTTP e BFF

`frontend/src/lib/api.ts` cria uma instância Axios com base em `/api/backend/`. O navegador não recebe nem envia manualmente o access token.

O fluxo é:

```text
Componente
→ feature hook/controller
→ service
→ cliente Axios em /api/backend/
→ BFF Next.js
→ API Django REST Framework
```

O interceptor:

- envia cookies com `withCredentials`;
- adiciona o token CSRF em métodos inseguros;
- remove qualquer header `Authorization` criado no navegador;
- coordena refresh de sessão em single flight;
- redireciona para login após falha definitiva de renovação;
- trata estados de assinatura retornados pelo backend.

## Sessão e navegação

Os endpoints em `/api/auth/` realizam login, refresh e logout no servidor Next.js. Tokens ficam em cookies HttpOnly e não são persistidos em `localStorage` ou `sessionStorage`.

O `AuthProvider` mantém apenas o perfil e o estado necessário para a interface. Middleware, menus e checks de role melhoram a experiência, mas não são fronteiras de autorização. Toda decisão de acesso continua no backend.

## Estado remoto

TanStack Query é usado para:

- carregamento e cache;
- invalidação após mutations;
- retry controlado;
- estados de loading e erro;
- isolamento das chamadas em hooks de feature.

Componentes visuais não devem chamar Axios, `fetch` ou services diretamente quando a operação pertence a um fluxo reutilizável.

## Componentização aplicada

Os principais fluxos refatorados são:

- modal de agendamento;
- editor de evolução clínica;
- wizard de checkout.

Cada um mantém o arquivo principal como composição e delega estado, contratos, regras puras e seções para arquivos locais da feature.

## Segurança

- tokens em cookies HttpOnly;
- proteção CSRF para métodos inseguros;
- nenhum token em Web Storage;
- nenhuma autorização definitiva baseada somente na role da interface;
- dados clínicos não são enviados ao gateway de pagamento;
- preço e liberação de assinatura são validados pelo backend;
- idempotência do checkout é preservada no controller;
- conteúdo clínico não é persistido no navegador.

## Acessibilidade

- inputs possuem label ou nome acessível;
- erros usam `role="alert"` e `aria-describedby` quando aplicável;
- modais usam `role="dialog"` e `aria-modal`;
- fluxos clínicos preservam focus trap e retorno de foco;
- botões de ícone possuem `aria-label` descritivo.

## Build e qualidade

Scripts disponíveis:

- `npm run dev`;
- `npm run build`;
- `npm run start`;
- `npm run lint`;
- `npm run typecheck`;
- `npm test`;
- `npm run test:auth`;
- `npm run test:coverage`.

[Voltar](README.md)
