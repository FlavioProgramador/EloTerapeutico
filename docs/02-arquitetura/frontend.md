# Frontend

## Stack

- Next.js 16.2.9 com App Router;
- React 19.2.4;
- TypeScript 6;
- Tailwind CSS 4;
- TanStack Query para estado remoto;
- Axios para API;
- React Hook Form e Zod para formulários;
- Radix UI, Lucide e Framer Motion na interface.

## Organização

```text
frontend/src/
├── app/          # rotas e layouts
├── components/   # componentes compartilhados
├── contexts/     # autenticação e notificações
├── features/     # módulos por domínio
├── lib/          # cliente HTTP e utilitários
└── types/        # contratos TypeScript
```

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

## Cliente HTTP

`frontend/src/lib/api.ts` cria uma instância Axios com `NEXT_PUBLIC_API_URL`. Um interceptor envia o access token e outro coordena renovação silenciosa, evitando múltiplos refreshes simultâneos.

## Sessão e navegação

`AuthProvider` carrega o perfil em `/auth/me/`, mantém o usuário em contexto e gerencia login/logout. O middleware redireciona usuários não autenticados e restringe visualmente rotas por role.

### Limitação de segurança

Os tokens são gravados pelo JavaScript em cookies sem `HttpOnly`. O middleware e o cookie de role são controles de experiência, não uma fronteira de autorização. Toda decisão de acesso precisa permanecer no backend.

## Build e qualidade

Scripts disponíveis:

- `npm run dev`;
- `npm run build`;
- `npm run start`;
- `npm run lint`;
- `npm run typecheck`;
- `npm test`;
- `npm run test:coverage`.

[Voltar](README.md)
