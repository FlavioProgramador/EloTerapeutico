# Arquitetura Frontend — Elo Terapêutico

> Esta referência permanece para compatibilidade com links antigos. A documentação principal está em [02 — Arquitetura / Frontend](../02-arquitetura/frontend.md) e [Componentização do frontend](../02-arquitetura/componentizacao-frontend.md).

## Stack atual

- Next.js 16.2.11 com App Router;
- React 19.2.4;
- TypeScript 6;
- Tailwind CSS 4;
- TanStack Query 5;
- Axios por meio do BFF;
- React Hook Form e Zod nos fluxos que usam schema;
- Radix UI, Lucide e Framer Motion.

## Organização

```text
frontend/src/
├── app/          # rotas, layouts e endpoints BFF
├── components/   # design system e componentes compartilhados
├── contexts/     # contextos globais de interface
├── features/     # módulos por domínio
├── lib/          # cliente HTTP, sessão e utilitários
├── providers/    # providers raiz
└── types/        # contratos compartilhados
```

Dentro de uma feature, componentes complexos são organizados como:

```text
componente de composição
→ controller ou hook de fluxo
→ service
→ cliente HTTP /api/backend/
→ BFF Next.js
→ Django REST Framework
```

Seções visuais não chamam APIs diretamente. Regras puras, formatação e montagem de payload ficam em utilitários ou controllers da feature.

## Sessão e BFF

O cliente Axios usa `/api/backend/`. O BFF mantém tokens em cookies HttpOnly e encaminha autenticação ao backend. Métodos inseguros usam CSRF e o navegador não adiciona `Authorization`.

Não é permitido:

- armazenar tokens em `localStorage` ou `sessionStorage`;
- usar role da interface como autorização definitiva;
- contornar o BFF com um cliente HTTP paralelo;
- persistir conteúdo clínico no navegador.

## TanStack Query

TanStack Query mantém dados remotos, cache e invalidação. Estado local é reservado para campos ainda não enviados, etapa ativa, abertura de modal e feedback transitório.

Após mutations, invalide somente as chaves afetadas. Componentes de linha, célula ou seção não devem iniciar chamadas remotas por conta própria.

## Componentização verificada

A refatoração atual separa os seguintes fluxos:

- agendamento de consulta;
- editor de evolução clínica;
- checkout de assinatura.

Os arquivos principais atuam como composição; controllers coordenam o fluxo; componentes locais representam seções coesas.

## Qualidade

```bash
npm ci
npm run lint
npm run typecheck
npm test
npm run test:auth
npm run build
```

Testes estruturais complementam os testes funcionais para impedir que chamadas remotas e regras sensíveis voltem aos componentes de composição.
