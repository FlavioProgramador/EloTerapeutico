# Design System — Elo Terapêutico

## Filosofia

> "Confiança através da consistência."

O Design System do Elo Terapêutico é construído para transmitir **confiança, profissionalismo e acolhimento** — valores essenciais para uma plataforma clínica.

Prioridades:
- **Clareza sobre decoração**: Interfaces que comunicam, não que impressionam
- **Consistência** acima de originalidade por seção
- **Acessibilidade** como requisito, não opcional
- **Densidade informacional** adequada para uso profissional

---

## Paleta de Cores

### Light Mode — "Sálvia & Obsidian"

| Token | Valor HSL | Uso |
|---|---|---|
| `--background` | `140 12% 98%` | Fundo da aplicação |
| `--foreground` | `140 24% 12%` | Texto principal |
| `--card` | `0 0% 100%` | Fundo de cards |
| `--primary` | `154 50% 35%` | Verde Sálvia Clínico — CTAs principais |
| `--secondary` | `140 10% 93%` | Fundos secundários, chips |
| `--muted` | `140 10% 93%` | Backgrounds neutros |
| `--muted-foreground` | `140 10% 45%` | Texto secundário, placeholders |
| `--accent` | `195 40% 40%` | Azul Securitário — elementos de destaque |
| `--destructive` | `0 65% 45%` | Vermelho Sóbrio — erros e exclusões |
| `--border` | `140 8% 90%` | Bordas sutis |
| `--ring` | `154 50% 35%` | Focus rings |

### Dark Mode — "Obsidian Green"

| Token | Valor HSL | Uso |
|---|---|---|
| `--background` | `140 15% 6%` | Fundo escuro |
| `--foreground` | `140 10% 92%` | Texto claro |
| `--card` | `140 12% 9%` | Cards escuros |
| `--primary` | `154 52% 48%` | Verde Jade — mais luminoso no escuro |

---

## Tipografia

### Hierarquia

| Nível | Classe | Uso |
|---|---|---|
| Display | `text-2xl font-bold tracking-tight` | Títulos de página |
| Heading 1 | `text-xl font-bold` | Cabeçalhos de seção |
| Heading 2 | `text-lg font-semibold` | Subtítulos |
| Body | `text-sm` | Texto padrão |
| Caption | `text-xs` | Labels, metadata, hints |
| Code | `font-mono text-xs` | Dados técnicos (CPF, CRP) |

### Fonte

- **Primária**: `Outfit` (Google Fonts) — para headings e UI elements
- **Fallback**: `Inter`, `system-ui`, `sans-serif`

---

## Espaçamento

Sistema baseado em 4px grid (Tailwind padrão):

| Token | Valor | Uso |
|---|---|---|
| `space-1` | 4px | Espaçamento mínimo entre elementos irmãos |
| `space-2` | 8px | Padding interno de badges e chips |
| `space-3` | 12px | Gap entre ícone e texto |
| `space-4` | 16px | Padding padrão de cards e inputs |
| `space-6` | 24px | Gap entre grupos de formulário |
| `space-8` | 32px | Espaçamento entre seções |

---

## Border Radius

| Token | Valor | Uso |
|---|---|---|
| `--radius` | `0.5rem` | Componentes padrão (inputs, cards) |
| `rounded-md` | `0.375rem` | Badges, chips |
| `rounded-full` | `9999px` | Avatares, indicadores circulares |

> **Princípio**: Evitar arredondamentos excessivos (`rounded-2xl`, `rounded-3xl`) que dão aparência de protótipo não polido.

---

## Sombras

| Classe | Uso |
|---|---|
| `shadow-xs` | Cards em repouso |
| `shadow-sm` | Cards com hover |
| `shadow-md` | Modais e dropdowns |
| `shadow-lg` | Toasts e tooltips |

---

## Componentes

### Button

Variantes: `default`, `destructive`, `outline`, `ghost`

```tsx
<Button variant="default" isLoading={false} leftIcon={<Plus />}>
  Novo Paciente
</Button>
```

### Badge

Variantes: `success`, `warning`, `destructive`, `muted`, `primary`, `outline`

```tsx
<Badge variant="success">Ativo</Badge>
<Badge variant="warning">Em Espera</Badge>
```

### Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Título</CardTitle>
    <CardDescription>Subtítulo</CardDescription>
  </CardHeader>
  <CardContent>
    {/* conteúdo */}
  </CardContent>
</Card>
```

### Input

```tsx
<Input
  id="email"
  label="E-mail"
  type="email"
  aria-describedby="email-error"
  leftIcon={<Mail />}
  error="Campo obrigatório"
/>
```

### Skeleton (Loading States)

```tsx
<SkeletonTable lines={5} />
<SkeletonStat />
<SkeletonCard />
```

### EmptyState

```tsx
<EmptyState
  icon={Users}
  title="Nenhum paciente cadastrado"
  description="Cadastre seu primeiro paciente para começar."
  action={<Button>Novo Paciente</Button>}
/>
```

---

## Estados de Componentes

### Loading
- Use `Skeleton*` específico para o contexto (tabela, KPI, card)
- Nunca use spinner genérico em áreas de conteúdo

### Empty
- Todo componente de lista deve ter um `EmptyState` contextualizado
- O EmptyState deve ter uma ação primária quando possível

### Error
- Use `toast.error()` para erros de operação
- Para falhas de carregamento, exiba inline com `role="alert"`

### Disabled
- `opacity-50 cursor-not-allowed` em botões desabilitados
- Sempre adicionar `disabled` e `aria-disabled="true"`

---

## Acessibilidade

### Contraste mínimo (WCAG AA)
- Texto normal: 4.5:1
- Texto grande (18px+): 3:1
- Componentes de interface: 3:1

### Focus
- Todos os elementos interativos têm `focus:ring-2 focus:ring-ring focus:ring-offset-2`
- Nunca usar `outline: none` sem substituição visual

### Screen Readers
- Botões sem texto visível têm `aria-label`
- Campos têm `label` associado ou `aria-label`
- Mensagens de erro têm `role="alert"` e `aria-describedby`
- Modais têm `role="dialog"` e `aria-modal="true"`
