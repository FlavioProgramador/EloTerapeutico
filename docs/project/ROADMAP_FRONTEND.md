# ⚛️ Roadmap Completo – Frontend (Next.js)

Este roadmap cobre **todo o ciclo de desenvolvimento do frontend** do Elo Terapêutico, desde a estrutura base até funcionalidades avançadas de UX, testes e deploy na Azure.

> **Stack:** Next.js 14+ · TypeScript · Tailwind CSS · Shadcn UI · TanStack Query · React Hook Form · Zod · Playwright

---

## 📋 Índice

1. [Fase 1 – Setup & Design System](#fase-1--setup--design-system)
2. [Fase 2 – Autenticação & Middleware](#fase-2--autenticação--middleware)
3. [Fase 3 – Layout Base & Navegação](#fase-3--layout-base--navegação)
4. [Fase 4 – Dashboard Principal](#fase-4--dashboard-principal)
5. [Fase 5 – Módulo de Pacientes](#fase-5--módulo-de-pacientes)
6. [Fase 6 – Módulo de Prontuário Eletrônico](#fase-6--módulo-de-prontuário-eletrônico)
7. [Fase 7 – Módulo de Agenda](#fase-7--módulo-de-agenda)
8. [Fase 8 – Módulo Financeiro](#fase-8--módulo-financeiro)
9. [Fase 9 – Notificações & Preferências](#fase-9--notificações--preferências)
10. [Fase 10 – UX Avançado & Acessibilidade](#fase-10--ux-avançado--acessibilidade)
11. [Fase 11 – Testes & Qualidade](#fase-11--testes--qualidade)
12. [Fase 12 – Deploy & Produção na Azure](#fase-12--deploy--produção-na-azure)

---

## Fase 1 – Setup & Design System

**Objetivo:** Criar a fundação visual e estrutural do projeto, garantindo consistência e escalabilidade desde o início.

### 1.1 Estrutura de Pastas
```
frontend/
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── (auth)/                 # Rotas públicas: login, register, reset
│   │   ├── (dashboard)/            # Rotas protegidas pelo middleware
│   │   │   ├── layout.tsx          # Layout com sidebar e header
│   │   │   ├── page.tsx            # Dashboard principal
│   │   │   ├── pacientes/          # Módulo de pacientes
│   │   │   ├── agenda/             # Módulo de agenda
│   │   │   ├── financeiro/         # Módulo financeiro
│   │   │   └── configuracoes/      # Configurações do perfil
│   │   ├── layout.tsx              # Root layout com providers
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                     # Componentes Shadcn UI gerados
│   │   ├── shared/                 # Componentes reutilizáveis
│   │   │   ├── PageHeader.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── ConfirmDialog.tsx
│   │   └── forms/                  # Formulários reutilizáveis
│   ├── hooks/                      # React hooks customizados
│   ├── services/                   # Funções de chamadas à API
│   ├── stores/                     # Zustand stores (estado global)
│   ├── types/                      # Interfaces e tipos TypeScript
│   ├── lib/                        # Utilitários, helpers, configurações
│   │   ├── api.ts                  # Instância do Axios configurada
│   │   ├── validators.ts           # Schemas Zod para validação de formulários
│   │   └── utils.ts                # Funções utilitárias (formatação de datas, moeda)
│   └── middleware.ts               # Middleware de proteção de rotas
├── public/
├── .env.local
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── Dockerfile
```

### 1.2 Design System (Tokens)

```typescript
// tailwind.config.ts – Paleta do Elo Terapêutico
colors: {
  primary:    { DEFAULT: '#4F6EF7', light: '#7B93F9', dark: '#3451D1' },
  secondary:  { DEFAULT: '#10B981', light: '#34D399', dark: '#059669' },
  surface:    { DEFAULT: '#FFFFFF', muted: '#F8FAFC', subtle: '#F1F5F9' },
  border:     { DEFAULT: '#E2E8F0', strong: '#CBD5E1' },
  text:       { primary: '#0F172A', secondary: '#475569', muted: '#94A3B8' },
  danger:     { DEFAULT: '#EF4444', light: '#FCA5A5' },
  warning:    { DEFAULT: '#F59E0B', light: '#FCD34D' },
}
```

### 1.3 Tipografia
- **Fonte principal:** `Inter` (via Google Fonts ou `next/font`)
- **Escala:** `text-xs` (12px) até `text-4xl` (36px)

### 1.4 Tarefas
- [ ] Inicializar Next.js 14 com TypeScript e App Router: `npx create-next-app@latest ./`
- [ ] Instalar e configurar Tailwind CSS com tokens de design customizados
- [ ] Instalar Shadcn UI: `npx shadcn-ui@latest init`
- [ ] Instalar componentes Shadcn necessários: Button, Card, Dialog, Input, Select, Table, Badge, Avatar, Dropdown, Tooltip, Toast
- [ ] Instalar `TanStack Query` e configurar `QueryClientProvider` no root layout
- [ ] Instalar `React Hook Form` + `Zod` para validação de formulários
- [ ] Instalar `Axios` e criar instância base em `src/lib/api.ts` com interceptors de token e erro
- [ ] Instalar `Zustand` para estado global (usuário autenticado, notificações)
- [ ] Configurar `next/font` com `Inter`
- [ ] Criar `globals.css` com CSS variables de design tokens
- [ ] Configurar `tsconfig.json` com paths absolutos (`@/components`, `@/services`, etc.)
- [ ] Configurar ESLint + Prettier com regras do projeto

---

## Fase 2 – Autenticação & Middleware

**Objetivo:** Implementar fluxo seguro de autenticação com JWT em cookies HttpOnly e proteção de rotas via middleware.

### 2.1 Fluxo de Autenticação

```
Usuário acessa /dashboard
        ↓
middleware.ts verifica cookie 'access_token'
        ↓
Token ausente? → Redirect para /login
        ↓
Token presente mas expirado? → Chama /api/auth/token/refresh/ via Server Action
        ↓
Refresh ok? → Continua. Falhou? → Redirect para /login
```

### 2.2 Páginas de Autenticação

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/login` | `LoginPage` | Formulário de e-mail e senha |
| `/cadastro` | `RegisterPage` | Cadastro de novo terapeuta |
| `/recuperar-senha` | `ForgotPasswordPage` | Envio de e-mail de recuperação |
| `/nova-senha` | `ResetPasswordPage` | Definição da nova senha via token |

### 2.3 Tarefas
- [ ] Criar página `/login` com formulário validado por Zod
- [ ] Implementar Server Action `loginAction()` que faz POST na API e seta cookies HttpOnly
- [ ] Criar Server Action `logoutAction()` que limpa os cookies e redireciona para `/login`
- [ ] Criar `middleware.ts` para proteger todas as rotas `/(dashboard)/*`
- [ ] Implementar refresh automático de token via middleware (interceptor do Axios)
- [ ] Criar Zustand store `useAuthStore` com dados do usuário autenticado
- [ ] Criar hook `useCurrentUser()` que lê o store e expõe dados do terapeuta logado
- [ ] Criar página de cadastro com campos: nome, e-mail, CRP, especialidade, senha
- [ ] Criar páginas de recuperação e redefinição de senha
- [ ] Implementar feedback visual de erro (credenciais inválidas, conta bloqueada)

---

## Fase 3 – Layout Base & Navegação

**Objetivo:** Criar o shell visual da aplicação: sidebar responsiva, header e sistema de navegação.

### 3.1 Estrutura do Layout

```
┌─────────────────────────────────────────────────────┐
│  HEADER: Logo | Busca global | Notificações | Avatar │
├───────────────┬─────────────────────────────────────┤
│               │                                     │
│   SIDEBAR     │         CONTENT AREA                │
│               │   (página atual renderizada)        │
│  Dashboard    │                                     │
│  Pacientes    │                                     │
│  Agenda       │                                     │
│  Financeiro   │                                     │
│  ─────────    │                                     │
│  Configurações│                                     │
│  Sair         │                                     │
│               │                                     │
└───────────────┴─────────────────────────────────────┘
```

### 3.2 Componentes do Layout

| Componente | Responsabilidade |
|-----------|-----------------|
| `Sidebar` | Navegação principal, collapse em mobile, indicador de rota ativa |
| `Header` | Busca global, ícone de notificações com badge, menu de perfil |
| `MobileNav` | Drawer/bottom nav para telas pequenas |
| `Breadcrumb` | Caminho de navegação hierárquico |
| `ThemeToggle` | Alternância entre tema claro e escuro |

### 3.3 Tarefas
- [ ] Criar `(dashboard)/layout.tsx` com Sidebar e Header
- [ ] Implementar `Sidebar` colapsável (ícones + labels) com `localStorage` para persistir estado
- [ ] Implementar navegação responsiva (sidebar em desktop, drawer em mobile)
- [ ] Implementar `Header` com avatar do terapeuta, dropdown de perfil e ícone de notificações
- [ ] Criar `ThemeToggle` e configurar suporte a dark mode via Tailwind `class` strategy
- [ ] Implementar `Breadcrumb` dinâmico baseado na rota atual
- [ ] Adicionar animações de transição de página com `framer-motion`
- [ ] Garantir que o layout é totalmente responsivo (mobile-first)

---

## Fase 4 – Dashboard Principal

**Objetivo:** Criar a página inicial informativa com KPIs do dia, gráficos e acesso rápido às funções principais.

### 4.1 Seções do Dashboard

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Consultas   │  Faturamento │  Pacientes   │  Taxa de     │
│  Hoje: 5     │  Mês: R$4.2k │  Ativos: 32  │  Presença 87%│
└──────────────┴──────────────┴──────────────┴──────────────┘

┌──────────────────────────┬────────────────────────────────┐
│  Agenda de Hoje          │  Atividade Recente             │
│  ─────────────           │  ─────────────                 │
│  09:00 – Ana Lima        │  • João faltou (ontem 14:00)   │
│  10:00 – Carlos Souza    │  • Maria pagou R$250           │
│  11:00 – Vaga            │  • Prontuário de Ana atualizado│
│  14:00 – Pedro Alves     │  • Nova sessão agendada        │
└──────────────────────────┴────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Faturamento dos últimos 6 meses (gráfico de barras)       │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Tarefas
- [ ] Criar componente `KpiCard` com valor, label, ícone e variação percentual
- [ ] Implementar 4 KPIs: consultas hoje, faturamento do mês, pacientes ativos, taxa de presença
- [ ] Criar componente `AgendaHoje` listando as próximas consultas do dia
- [ ] Criar componente `AtividadeRecente` com feed das últimas ações
- [ ] Integrar `recharts` ou `chart.js` para o gráfico de faturamento mensal
- [ ] Usar `TanStack Query` com `staleTime` para cache eficiente dos dados do dashboard
- [ ] Implementar skeleton loading para todos os cards e gráficos
- [ ] Criar atalhos rápidos: "Novo Paciente", "Agendar Consulta", "Registrar Pagamento"

---

## Fase 5 – Módulo de Pacientes

**Objetivo:** Interface completa para gestão de pacientes com listagem, busca, cadastro e visualização de perfil.

### 5.1 Telas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/pacientes` | `PatientsPage` | Listagem com busca e filtros |
| `/pacientes/novo` | `NewPatientPage` | Formulário de cadastro |
| `/pacientes/[id]` | `PatientDetailPage` | Perfil completo do paciente |
| `/pacientes/[id]/editar` | `EditPatientPage` | Edição dos dados do paciente |

### 5.2 Componentes

| Componente | Descrição |
|-----------|-----------|
| `PatientCard` | Card compacto com avatar, nome, status e próxima consulta |
| `PatientTable` | Tabela com ordenação e paginação |
| `PatientFilter` | Filtros por status, período de cadastro e terapeuta |
| `PatientForm` | Formulário com validação Zod (dados pessoais, endereço, contato) |
| `PatientStatusBadge` | Badge colorido: Ativo (verde), Inativo (cinza), Alta (azul) |
| `PatientTimeline` | Timeline cronológica de consultas, evoluções e pagamentos |
| `PatientSummaryCard` | Card de resumo no topo do perfil (foto, nome, CPF, telefone) |

### 5.3 Tarefas
- [ ] Criar `PatientsPage` com listagem via `TanStack Query`
- [ ] Implementar busca com debounce de 300ms (evitar excesso de requisições)
- [ ] Implementar filtros por status e paginação
- [ ] Criar `PatientForm` com todos os campos e validação Zod
- [ ] Integrar busca de endereço por CEP via API ViaCEP
- [ ] Criar `PatientDetailPage` com abas: **Resumo | Prontuário | Agenda | Financeiro | Documentos**
- [ ] Implementar `PatientTimeline` com scroll infinito
- [ ] Criar modal de confirmação para desativação de paciente
- [ ] Implementar upload de foto de perfil do paciente
- [ ] Implementar upload de documentos (PDF) com preview

---

## Fase 6 – Módulo de Prontuário Eletrônico

**Objetivo:** Interface intuitiva para criação e leitura de evoluções clínicas, com editor rico e histórico seguro.

### 6.1 Telas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/pacientes/[id]/prontuario` | `MedicalRecordPage` | Anamnese + Lista de evoluções |
| `/pacientes/[id]/prontuario/nova-evolucao` | `NewEvolutionPage` | Editor de nova evolução |
| `/pacientes/[id]/prontuario/[evolutionId]` | `EvolutionDetailPage` | Visualização de evolução |

### 6.2 Componentes

| Componente | Descrição |
|-----------|-----------|
| `AnamnesisForm` | Formulário de anamnese inicial (preenchido uma vez) |
| `EvolutionEditor` | Editor de texto rico (TipTap ou Quill) para digitação da sessão |
| `EvolutionCard` | Card resumido da evolução na listagem (data, CID, bloqueada?) |
| `EvolutionDetail` | Visualização completa da evolução (read-only se bloqueada) |
| `LockBadge` | Ícone de cadeado indicando que a evolução não pode mais ser editada |
| `AddendumForm` | Formulário de termo aditivo para evoluções bloqueadas |
| `CidSearch` | Campo de busca de CID-10 com autocomplete |

### 6.3 Tarefas
- [ ] Instalar e configurar `Tiptap` como editor de texto rico (bold, italic, listas, cabeçalhos)
- [ ] Criar `EvolutionEditor` com autosave a cada 30 segundos via Server Action
- [ ] Implementar indicador visual de "Salvando..." e "Salvo" no editor
- [ ] Criar `AnamnesisForm` em múltiplos steps (wizard) para facilitar o preenchimento inicial
- [ ] Implementar busca de CID-10 com autocomplete integrado à API
- [ ] Criar listagem de evoluções com paginação e filtro por data
- [ ] Exibir `LockBadge` em evoluções com mais de 48h
- [ ] Implementar formulário de `Addendum` com explicação clara do que é um termo aditivo
- [ ] Criar botão "Exportar PDF" que chama o endpoint do backend e faz download
- [ ] Garantir que evoluções bloqueadas exibem o texto como read-only com fundo diferenciado

---

## Fase 7 – Módulo de Agenda

**Objetivo:** Calendário interativo e intuitivo para visualização e gestão de consultas.

### 7.1 Telas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/agenda` | `AgendaPage` | Visão geral com calendário |
| `/agenda/nova` | `NewAppointmentPage` | Formulário de agendamento |
| `/agenda/[id]` | `AppointmentDetailPage` | Detalhes e ações de uma consulta |

### 7.2 Componentes

| Componente | Descrição |
|-----------|-----------|
| `CalendarView` | Calendário mensal/semanal/diário via `@fullcalendar/react` |
| `DayView` | Grade horária do dia com consultas no estilo Google Agenda |
| `AppointmentCard` | Card de consulta no calendário (cor por status) |
| `AppointmentForm` | Formulário de criação com seletor de paciente, horário e valor |
| `StatusDropdown` | Dropdown para alterar o status da consulta rapidamente |
| `TimeSlotPicker` | Seletor de horário que exibe apenas slots disponíveis |
| `AppointmentActions` | Ações rápidas: Confirmar, Faltou, Cancelar, Remarcar |

### 7.3 Mapa de Cores por Status

| Status | Cor |
|--------|-----|
| Aguardando | Azul claro |
| Confirmado | Verde |
| Faltou | Vermelho |
| Cancelado | Cinza |
| Remarcado | Amarelo |

### 7.4 Tarefas
- [ ] Instalar `@fullcalendar/react` e configurar com locale pt-BR
- [ ] Implementar visualizações: Mês, Semana e Dia
- [ ] Integrar `TanStack Query` para carregar eventos do calendário por intervalo de datas
- [ ] Implementar criação de consulta via clique em horário vazio no calendário
- [ ] Criar `AppointmentForm` com busca de paciente via autocomplete e `TimeSlotPicker`
- [ ] Implementar drag-and-drop para remarcar consultas (nativo do FullCalendar)
- [ ] Criar modal de detalhes ao clicar em uma consulta com ações rápidas
- [ ] Implementar recorrência (semanal/quinzenal/mensal) no formulário
- [ ] Criar `AgendaHoje` component reutilizável (também usado no Dashboard)
- [ ] Implementar notificação toast ao alterar status de uma consulta

---

## Fase 8 – Módulo Financeiro

**Objetivo:** Tela de controle financeiro com listagem de transações, resumo mensal e geração de recibos.

### 8.1 Telas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/financeiro` | `FinanceiroPage` | Listagem de transações e resumo |
| `/financeiro/nova` | `NewTransactionPage` | Registro manual de transação |

### 8.2 Componentes

| Componente | Descrição |
|-----------|-----------|
| `FinanceSummary` | Cards com: Total Recebido, A Receber, Total Despesas, Saldo |
| `TransactionTable` | Tabela com filtro por período, tipo e status de pagamento |
| `TransactionForm` | Formulário de nova transação (valor, tipo, método de pagamento) |
| `PaymentStatusBadge` | Badge: Pago (verde), Pendente (amarelo), Cancelado (cinza) |
| `RevenueChart` | Gráfico de linha de receitas vs. despesas por mês |
| `PendingPayments` | Lista de consultas com pagamento pendente com ação "Marcar como Pago" |

### 8.3 Tarefas
- [ ] Criar `FinanceiroPage` com resumo mensal via KPI cards
- [ ] Implementar tabela de transações com filtro por período (date picker de range)
- [ ] Criar `TransactionForm` para registro manual
- [ ] Implementar ação "Marcar como Pago" diretamente na tabela (sem abrir modal)
- [ ] Integrar gráfico de receita mensal (últimos 6 meses)
- [ ] Criar `PendingPayments` com listagem de consultas a receber
- [ ] Implementar download de recibo via botão na tabela (chama API, baixa PDF)
- [ ] Criar exportação de extrato por período em CSV

---

## Fase 9 – Notificações & Preferências

**Objetivo:** Centro de notificações em tempo real e tela de configurações do terapeuta.

### 9.1 Notificações

- [ ] Criar `NotificationCenter` (dropdown no Header com lista de notificações recentes)
- [ ] Implementar badge com contagem de notificações não lidas
- [ ] Integrar **Server-Sent Events (SSE)** ou polling via `TanStack Query` para notificações em tempo real
- [ ] Criar página `/notificacoes` com histórico completo

### 9.2 Configurações (`/configuracoes`)

| Aba | Conteúdo |
|-----|---------|
| **Perfil** | Foto, nome, CRP, especialidade, bio, telefone |
| **Segurança** | Alterar senha, sessões ativas |
| **Agenda** | Duração padrão de sessão, horários de atendimento por dia da semana, valor padrão da sessão |
| **Notificações** | Habilitar/desabilitar lembretes por e-mail e WhatsApp |
| **Conta** | Plano atual, exportar dados, excluir conta |

### 9.3 Tarefas
- [ ] Criar `NotificationCenter` com dropdown no Header
- [ ] Criar página de configurações com abas (Shadcn `Tabs`)
- [ ] Criar formulário de edição de perfil com upload de avatar
- [ ] Criar formulário de horários de atendimento (grade semanal interativa)
- [ ] Implementar troca de senha com validação de senha atual
- [ ] Criar toggle de preferências de notificação

---

## Fase 10 – UX Avançado & Acessibilidade

**Objetivo:** Polir a experiência do usuário com micro-interações, feedback visual e conformidade com WCAG 2.1.

### 10.1 Micro-interações & Animações
- [ ] Adicionar transições suaves entre páginas com `framer-motion`
- [ ] Implementar feedback de loading com skeletons customizados para cada módulo
- [ ] Adicionar animações de entrada (fade-in, slide-up) nos cards e listas
- [ ] Implementar toast notifications globais para ações de sucesso, erro e aviso

### 10.2 Acessibilidade (WCAG 2.1 – nível AA)
- [ ] Garantir contraste mínimo de 4.5:1 em todos os textos
- [ ] Todos os formulários com labels, aria-describedby para erros e aria-required
- [ ] Navegação completa por teclado (Tab, Shift+Tab, Enter, Esc)
- [ ] Componentes Shadcn UI já possuem acessibilidade via Radix UI — verificar customizações
- [ ] Adicionar `focus-visible` styles customizados
- [ ] Testar com leitor de telas (NVDA ou VoiceOver)

### 10.3 Performance
- [ ] Implementar `next/image` para todas as imagens com `priority` nos above-the-fold
- [ ] Usar `dynamic()` do Next.js para lazy loading do calendário e editor de texto
- [ ] Configurar `TanStack Query` com `staleTime` e `gcTime` adequados para evitar refetches desnecessários
- [ ] Analisar bundle com `@next/bundle-analyzer`
- [ ] Garantir Lighthouse score > 90 em Performance, Acessibilidade e SEO

---

## Fase 11 – Testes & Qualidade

**Objetivo:** Garantir confiabilidade com testes de componentes e E2E cobrindo os fluxos críticos.

### 11.1 Estratégia de Testes

| Tipo | Ferramenta | Foco |
|------|-----------|------|
| Componente | `Jest` + `Testing Library` | Renderização, interação, estados de loading/erro |
| Integração | `MSW` (Mock Service Worker) | Mocking de chamadas à API Django |
| E2E | `Playwright` | Fluxos críticos: login, cadastrar paciente, agendar consulta |

### 11.2 Fluxos E2E Prioritários

- [ ] **Login e logout** – usuário válido e credenciais inválidas
- [ ] **Cadastrar novo paciente** – formulário completo com validações
- [ ] **Criar evolução clínica** – editor, salvar e verificar bloqueio após 48h
- [ ] **Agendar consulta** – criar, alterar status e cancelar
- [ ] **Registrar pagamento** – marcar sessão como paga e baixar recibo

### 11.3 Tarefas
- [ ] Configurar `Jest` e `@testing-library/react` com suporte a TypeScript
- [ ] Configurar `MSW` para interceptar e mockar chamadas à API
- [ ] Criar testes de componente para: `PatientForm`, `EvolutionEditor`, `AppointmentCard`
- [ ] Configurar `Playwright` e criar `playwright.config.ts`
- [ ] Criar `e2e/auth.spec.ts`, `e2e/patients.spec.ts`, `e2e/appointments.spec.ts`
- [ ] Configurar GitHub Actions para rodar testes em todo PR
- [ ] Gerar relatório de cobertura e manter acima de 70%

---

## Fase 12 – Deploy & Produção na Azure

**Objetivo:** Publicar o frontend na Azure com deploy automatizado, variáveis de ambiente seguras e performance otimizada.

### 12.1 Opções de Hospedagem na Azure

| Opção | Quando usar |
|-------|------------|
| **Azure Static Web Apps** | Se o Next.js for exportado como estático (`next export`) — gratuito |
| **Azure App Service (Node.js)** | Se usar SSR, Server Actions ou API Routes — recomendado |

> **Recomendação:** Azure App Service (Node.js) para aproveitar todas as funcionalidades do App Router.

### 12.2 Configurações de Produção

- [ ] Definir `NEXT_PUBLIC_API_URL` e outras variáveis em **Azure App Service > Configuration**
- [ ] Garantir que `next.config.js` tem `output: 'standalone'` para produção
- [ ] Configurar `NEXTAUTH_URL` (se usar next-auth) e cookies seguros
- [ ] Habilitar compressão GZIP no App Service

### 12.3 GitHub Actions – Deploy Frontend

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with: { node-version: '18' }
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --watchAll=false --coverage
      - run: npx playwright install --with-deps
      - run: npx playwright test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with: { node-version: '18' }
      - run: npm ci
      - run: npm run build
      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ secrets.AZURE_FRONTEND_APP_NAME }}
          publish-profile: ${{ secrets.AZURE_FRONTEND_PUBLISH_PROFILE }}
          package: .next/standalone
```

### 12.4 Tarefas
- [ ] Configurar `next.config.js` com `output: 'standalone'`
- [ ] Criar workflow `.github/workflows/deploy-frontend.yml`
- [ ] Definir todas as variáveis de ambiente no Azure App Service
- [ ] Validar que o `middleware.ts` funciona corretamente em produção
- [ ] Configurar domínio customizado e certificado SSL no Azure
- [ ] Testar performance em produção com Lighthouse CI

---

## 🗓️ Cronograma Resumido

| Fase | Duração Estimada | Prioridade |
|------|:----------------:|:----------:|
| 1 – Setup & Design System | 3 dias | 🔴 Alta |
| 2 – Autenticação & Middleware | 4 dias | 🔴 Alta |
| 3 – Layout Base & Navegação | 4 dias | 🔴 Alta |
| 4 – Dashboard Principal | 3 dias | 🔴 Alta |
| 5 – Módulo de Pacientes | 6 dias | 🔴 Alta |
| 6 – Prontuário Eletrônico | 6 dias | 🔴 Alta |
| 7 – Módulo de Agenda | 7 dias | 🔴 Alta |
| 8 – Módulo Financeiro | 4 dias | 🟡 Média |
| 9 – Notificações & Preferências | 4 dias | 🟡 Média |
| 10 – UX Avançado & Acessibilidade | 4 dias | 🟡 Média |
| 11 – Testes & Qualidade | Contínuo | 🔴 Alta |
| 12 – Deploy & Produção | 3 dias | 🔴 Alta |

> 📌 **Total estimado:** ~48 dias úteis de desenvolvimento solo.

---

## 🔗 Referências Rápidas

| Recurso | Link |
|---------|------|
| Next.js App Router Docs | https://nextjs.org/docs |
| Tailwind CSS | https://tailwindcss.com/docs |
| Shadcn UI | https://ui.shadcn.com |
| TanStack Query | https://tanstack.com/query/latest |
| FullCalendar React | https://fullcalendar.io/docs/react |
| Tiptap Editor | https://tiptap.dev |
| Playwright Docs | https://playwright.dev |
| React Hook Form | https://react-hook-form.com |
| Zod | https://zod.dev |
