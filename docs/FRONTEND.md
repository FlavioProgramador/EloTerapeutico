# Arquitetura Frontend — Elo Terapêutico

## Visão Geral

O frontend é construído em **Next.js 15+ (App Router)** com TypeScript, Tailwind CSS v4 e uma arquitetura **feature-based** que separa responsabilidades por domínio.

---

## Estrutura de Diretórios

```
frontend/src/
├── app/                          # App Router (Next.js)
│   ├── layout.tsx                # Root layout com Providers
│   ├── page.tsx                  # Landing page pública
│   ├── login/page.tsx            # Tela de login
│   ├── register/page.tsx         # Tela de registro
│   └── dashboard/
│       ├── layout.tsx            # Layout do dashboard autenticado
│       ├── page.tsx              # Dashboard principal (KPIs)
│       ├── patients/page.tsx     # CRM de pacientes
│       ├── agenda/page.tsx       # Calendário de consultas
│       ├── records/page.tsx      # Prontuários/Evoluções
│       └── financeiro/page.tsx   # Controle financeiro
│
├── components/
│   ├── ui/                       # Design System base
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── modal.tsx
│   │   ├── table.tsx
│   │   ├── badge.tsx             # [NOVO] Badges de status tipados
│   │   ├── skeleton.tsx          # [NOVO] Loading states estruturados
│   │   └── empty-state.tsx       # [NOVO] Estados vazios contextuais
│   └── navigation/               # Componentes de navegação
│
├── contexts/
│   └── auth.tsx                  # AuthContext (estado global de autenticação)
│
├── features/                     # [NOVO] Feature-based modules
│   ├── auth/
│   │   ├── schemas/auth.schemas.ts
│   │   └── services/auth.service.ts
│   ├── patients/
│   │   ├── hooks/use-patients.ts
│   │   ├── schemas/patient.schemas.ts
│   │   └── services/patients.service.ts
│   ├── agenda/
│   │   ├── hooks/use-agenda.ts
│   │   ├── schemas/appointment.schemas.ts
│   │   └── services/agenda.service.ts
│   ├── records/
│   │   ├── hooks/use-records.ts
│   │   └── services/records.service.ts
│   └── financeiro/
│       ├── hooks/use-financeiro.ts
│       ├── schemas/transaction.schemas.ts
│       └── services/financeiro.service.ts
│
├── lib/
│   ├── api.ts                    # Instância Axios + interceptores JWT
│   └── utils.ts                  # [EXPANDIDO] Utilitários de frontend
│
├── providers/                    # [NOVO] Providers raiz
│   ├── providers.tsx             # Providers unificados
│   ├── query-client.ts           # Configuração TanStack Query
│   └── theme-provider.tsx        # Dark mode (next-themes)
│
├── types/
│   └── index.ts                  # [NOVO] Tipos TypeScript de domínio
│
├── constants/
│   └── index.ts                  # [NOVO] Query Keys, labels, rotas
│
└── middleware.ts                 # RBAC + proteção de rotas
```

---

## Stack Técnica

| Camada | Tecnologia | Propósito |
|--------|-----------|-----------|
| Framework | Next.js 15 (App Router) | SSR, roteamento, layouts aninhados |
| Linguagem | TypeScript | Tipagem fim-a-fim |
| Estilização | Tailwind CSS v4 | Tokens de design, utilitários |
| Estado do Servidor | TanStack Query v5 | Cache, sync, invalidação automática |
| Formulários | React Hook Form + Zod | Validação declarativa com schemas |
| Auth | JWT via cookies (httpOnly + sameSite) | Sessão segura |
| Notificações | Sonner | Toasts acessíveis e não-bloqueantes |
| Dark Mode | next-themes | Suporte a tema via CSS class |
| Animações | Framer Motion | Micro-animações performáticas |
| HTTP Client | Axios + interceptores | Auto-refresh de tokens JWT |

---

## Fluxo de Dados

```
Componente/Page
    │
    ├── useQuery/useMutation (TanStack Query)
    │       │
    │       └── Feature Hook (ex: usePatients)
    │               │
    │               └── Service (ex: patientsService.list)
    │                       │
    │                       └── api (Axios instance)
    │                               │
    │                               └── Django REST API
    │
    └── useForm + zodResolver (React Hook Form)
            │
            └── Zod Schema (validação client-side)
```

---

## Padrões de Código

### Query Keys
Todas as queries usam as constantes de `@/constants`:

```typescript
// Nunca use strings literais:
// ❌ useQuery({ queryKey: ["patients"] })

// ✅ Use as constantes:
useQuery({ queryKey: QUERY_KEYS.patients })
useQuery({ queryKey: QUERY_KEYS.patient(id) })
```

### Invalidação de Cache
Após mutações, invalide apenas as queries afetadas:

```typescript
// ✅ Invalida lista + item específico
queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients });
queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patient(id) });
```

### Error Handling
Use `extractApiError` de `@/lib/utils` para extrair mensagens de erro da API DRF:

```typescript
onError: (error) => {
  toast.error(extractApiError(error));
}
```

---

## Segurança

- **RBAC**: Middleware Next.js valida role do usuário por cookie
- **JWT**: Access token (30min) + Refresh token (7d) armazenados em cookies `sameSite: lax`
- **Auto-refresh**: Interceptor Axios renova silenciosamente tokens expirados
- **LGPD**: Campos clínicos sensíveis são criptografados no backend (Fernet)

---

## Acessibilidade (WCAG AA)

- Todos os inputs têm `aria-label` ou `label` associado
- Erros de formulário usam `aria-describedby` + `role="alert"`
- Modais usam `role="dialog"` com `aria-modal="true"`
- Botões de ícone têm `aria-label` descritivo
- Empty states e skeletons têm `role="status"`
