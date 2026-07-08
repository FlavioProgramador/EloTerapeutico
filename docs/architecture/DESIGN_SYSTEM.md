# Design System — Elo Terapêutico

## Direção visual

> **Acolhimento Seguro:** confiança clínica com aparência tecnológica madura.

A interface deve transmitir profissionalismo, calma e segurança sem parecer fria ou produzida por um gerador genérico de dashboards.

Princípios:

- clareza antes de decoração;
- azul clínico para identidade principal, ações importantes e seleção;
- azul/ciano luminoso para informação, segurança e apoio;
- verde/esmeralda apenas para indicação de sucesso/confirmação;
- superfícies neutras com contraste progressivo;
- bordas finas e sombras discretas;
- gradientes apenas quando comunicarem progresso ou seleção;
- nenhuma informação clínica deve depender apenas da cor.

---

## Paleta semântica

A implementação oficial fica em `frontend/src/app/globals.css`. Componentes devem usar tokens como `bg-card`, `text-foreground` e `border-border`, nunca repetir valores HSL ou HEX diretamente.

### Tema claro

| Token | HSL | HEX aproximado | Uso |
|---|---:|---:|---|
| `--background` | `220 20% 97%` | `#F1F3F5` | Fundo geral do app |
| `--background-subtle` | `220 25% 95%` | `#E9ECEF` | Fundo secundário / apoio |
| `--foreground` | `222 47% 15%` | `#1A2536` | Texto padrão |
| `--card` | `0 0% 100%` | `#FFFFFF` | Cards e painéis |
| `--primary` | `221 83% 53%` | `#2563EB` | Cor primária padrão |
| `--primary-hover` | `221 84% 48%` | `#1D4ED8` | Hover da cor primária |
| `--primary-active` | `221 84% 42%` | `#1E40AF` | Clique / ativo da cor primária |
| `--primary-soft` | `221 95% 94%` | `#EFF6FF` | Fundo suave / tags de seleção |
| `--secondary` | `220 14% 96%` | `#F1F5F9` | Botões secundários |
| `--border` | `220 13% 91%` | `#E2E8F0` | Bordas padrão |
| `--border-strong` | `220 13% 80%` | `#CBD5E1` | Divisores e bordas fortes |
| `--text-primary` | `222 47% 15%` | `#1E293B` | Texto de alto contraste |
| `--text-secondary` | `220 16% 36%` | `#475569` | Texto de médio contraste |
| `--text-muted` | `220 14% 56%` | `#64748B` | Rótulos e placeholders |
| `--success` | `142 72% 29%` | `#15803D` | Sucesso primário |
| `--success-soft` | `142 72% 95%` | `#F0FDF4` | Badge / tag de sucesso |
| `--warning` | `38 92% 44%` | `#B45309` | Alerta primário |
| `--warning-soft` | `38 92% 95%` | `#FEF3C7` | Badge / tag de alerta |
| `--danger` | `0 74% 42%` | `#B91C1C` | Erro e destrutivo |
| `--danger-soft` | `0 74% 96%` | `#FEF2F2` | Badge / tag de erro |

### Tema escuro

| Token | HSL | HEX aproximado | Uso |
|---|---:|---:|---|
| `--background` | `222 47% 6%` | `#090D16` | Fundo escuro principal |
| `--background-subtle` | `222 47% 4%` | `#06090F` | Fundo escuro de apoio |
| `--foreground` | `210 40% 98%` | `#F8FAFC` | Texto padrão |
| `--card` | `222 47% 10%` | `#0F172A` | Cards e painéis |
| `--primary` | `217 91% 65%` | `#60A5FA` | Cor primária padrão no escuro |
| `--primary-hover` | `217 91% 70%` | `#93C5FD` | Hover da cor primária |
| `--primary-soft` | `217 91% 15%` | `#1E3A8A` | Fundo suave / tags no escuro |
| `--secondary` | `222 47% 12%` | `#1E293B` | Ações secundárias |
| `--border` | `222 47% 15%` | `#1E293B` | Bordas e divisores |
| `--border-strong` | `222 47% 24%` | `#334155` | Bordas destacadas |
| `--text-primary` | `210 40% 98%` | `#F8FAFC` | Texto principal |
| `--text-secondary` | `215 20% 80%` | `#CBD5E1` | Texto de apoio |
| `--text-muted` | `215 16% 60%` | `#94A3B8` | Textos apagados |
| `--success` | `142 70% 45%` | `#22C55E` | Sucesso no escuro |
| `--success-soft` | `142 70% 12%` | `#14532D` | Badge de sucesso no escuro |
| `--danger` | `0 84% 60%` | `#EF4444` | Erro no escuro |
| `--danger-soft` | `0 84% 15%` | `#7F1D1D` | Badge de erro no escuro |

### Estados

| Token | Finalidade |
|---|---|
| `success` | operação concluída, pagamento recebido, registro ativo |
| `warning` | atenção, prazo próximo, pendência não bloqueante |
| `info` | ajuda, segurança, informação contextual |
| `destructive` | erro, cancelamento, exclusão ou bloqueio |

Não use `primary` para avisos, pendências ou erros. Estados devem combinar cor, ícone e texto.

### Navegação lateral

A barra lateral permanece escura nos dois temas para criar referência espacial estável:

- `sidebar`: fundo principal;
- `sidebar-surface`: hover e bloco de perfil;
- `sidebar-foreground`: texto principal;
- `sidebar-muted`: texto e ícones em repouso;
- `sidebar-active`: item ativo, foco e marca;
- `sidebar-border`: divisores.

---

## Regras de aplicação

### Hierarquia de superfícies

1. `background`: plano mais distante;
2. `surface`: agrupamentos discretos;
3. `card`: conteúdo principal;
4. `popover`: menus, dropdowns e modais.

Evite empilhar cards dentro de cards sem necessidade. Para agrupamentos internos, prefira borda ou `bg-muted/40`.

### Uso de cores

- uma ação primária por região visual;
- no máximo duas cores de destaque simultâneas;
- ícones herdam a cor do contexto;
- textos longos usam `foreground` ou `muted-foreground`;
- barras de progresso usam `primary`, exceto quando representam alerta ou erro;
- badges devem ser compactos e usar transparência baixa no fundo.

### Gradientes e efeitos

- evitar gradientes decorativos grandes;
- permitir gradiente curto entre `primary` e `accent` para progresso ou seleção;
- não usar blur ou glassmorphism em cards comuns;
- sombras devem indicar elevação real, não ornamentação.

---

## Tipografia

Fonte principal: `Outfit`, com fallback para `Inter`, `system-ui` e `sans-serif`.

| Nível | Classe de referência | Uso |
|---|---|---|
| Título de página | `text-2xl font-bold tracking-tight` | Nome da tela |
| Título de seção | `text-base font-semibold` | Blocos principais |
| Título de card | `text-sm font-semibold` | Cards e painéis |
| Corpo | `text-sm` | Conteúdo padrão |
| Metadado | `text-xs text-muted-foreground` | Datas, autores e apoio |
| Rótulo compacto | `text-[10px] font-semibold uppercase tracking-wide` | KPIs e tabelas densas |

Textos clínicos não devem usar tamanho inferior a `12px` em áreas de leitura prolongada.

---

## Geometria e espaçamento

O sistema usa grid de 4px.

| Token | Valor | Uso |
|---|---:|---|
| `space-1` | 4px | Ajustes mínimos |
| `space-2` | 8px | Badges e ícones |
| `space-3` | 12px | Controles compactos |
| `space-4` | 16px | Padding padrão de cards |
| `space-6` | 24px | Separação de grupos |
| `space-8` | 32px | Seções de página |

`--radius` é `0.75rem`. Use:

- `rounded-md` para inputs e botões;
- `rounded-lg` para itens de navegação;
- `rounded-xl` para cards e modais;
- `rounded-full` apenas para avatar, status e progresso circular.

Evite `rounded-2xl` e `rounded-3xl` em interfaces operacionais.

---

## Componentes

### Botões

- `primary`: ação principal;
- `secondary`: ação de apoio;
- `outline`: ação neutra em superfície existente;
- `ghost`: ação de baixa prioridade;
- `destructive`: ação irreversível.

O texto do botão deve usar `text-primary-foreground`, nunca `text-white` fixo.

### Cards

Cards usam `bg-card`, `text-card-foreground`, `border-border` e sombra mínima. Hover só deve existir quando o card for clicável.

### Inputs

Inputs usam `bg-background` ou `bg-card`, `border-input` e foco com `ring`. Placeholder usa `muted-foreground` com opacidade reduzida.

### Badges

Badges apresentam status com fundo de 8% a 12% de opacidade, borda discreta e texto legível. Não usar badge como botão.

### Toasts

- sucesso: borda lateral `success`;
- informação: borda lateral `info`;
- atenção: borda lateral `warning`;
- erro: borda lateral `destructive`.

---

## Acessibilidade

- texto normal: contraste mínimo de `4.5:1`;
- texto grande e componentes: mínimo de `3:1`;
- foco visível em todos os controles;
- não remover outline sem substituição;
- estados sempre combinam texto, ícone e cor;
- respeitar `prefers-reduced-motion`;
- botões apenas com ícone exigem `aria-label`;
- mensagens de erro usam `role="alert"` quando apropriado.

Os pares principais foram escolhidos para atender WCAG AA nos usos previstos. Componentes novos devem ser verificados quando introduzirem opacidade ou sobreposição.

---

## Migração de componentes antigos

Existe uma ponte temporária em `globals.css` para classes que ainda contêm valores HSL literais. Todo código novo deve usar tokens semânticos. Ao editar uma tela antiga:

1. substitua valores `hsl(...)` por tokens;
2. remova cores fixas de texto em botões;
3. valide tema claro e escuro;
4. teste foco, hover, disabled e estados de erro;
5. remova o seletor de compatibilidade correspondente quando não houver mais consumidores.
