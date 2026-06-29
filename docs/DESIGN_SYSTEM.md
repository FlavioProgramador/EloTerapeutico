# Design System — Elo Terapêutico

## Direção visual

> **Acolhimento Seguro:** confiança clínica com aparência tecnológica madura.

A interface deve transmitir profissionalismo, calma e segurança sem parecer fria, excessivamente verde ou produzida por um gerador genérico de dashboards.

Princípios:

- clareza antes de decoração;
- verde somente para ações principais, sucesso e seleção;
- azul ardósia para informação, segurança e apoio;
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
| `--background` | `204 33% 97%` | `#F5F8FA` | Fundo geral |
| `--foreground` | `202 46% 12%` | `#10212B` | Texto principal |
| `--card` | `0 0% 100%` | `#FFFFFF` | Cards e painéis |
| `--primary` | `168 73% 30%` | `#15856F` | CTA, seleção e sucesso principal |
| `--primary-foreground` | `0 0% 100%` | `#FFFFFF` | Conteúdo sobre o primário |
| `--secondary` | `198 31% 94%` | `#EAF1F4` | Ações secundárias e superfícies de apoio |
| `--muted` | `195 29% 95%` | `#EDF3F5` | Fundos discretos |
| `--muted-foreground` | `205 15% 44%` | `#5F7280` | Texto secundário |
| `--accent` | `196 55% 40%` | `#2D7F9D` | Informação e segurança |
| `--border` | `200 25% 88%` | `#D9E3E8` | Bordas e divisores |
| `--destructive` | `0 61% 54%` | `#D14343` | Erros e ações destrutivas |

### Tema escuro

| Token | HSL | HEX aproximado | Uso |
|---|---:|---:|---|
| `--background` | `203 60% 7%` | `#07141C` | Fundo azul-petróleo neutro |
| `--foreground` | `191 35% 94%` | `#EAF3F5` | Texto principal |
| `--card` | `203 50% 10%` | `#0D1D27` | Cards e painéis |
| `--popover` | `202 48% 12%` | `#10232E` | Dropdowns e modais |
| `--primary` | `163 64% 52%` | `#34D3A5` | CTA, foco e seleção |
| `--primary-foreground` | `162 68% 7%` | `#062018` | Conteúdo sobre o primário |
| `--secondary` | `200 45% 14%` | `#142A35` | Ações secundárias |
| `--muted` | `201 46% 12%` | `#11242E` | Superfícies discretas |
| `--muted-foreground` | `199 19% 63%` | `#8FA7B2` | Texto secundário |
| `--accent` | `197 62% 61%` | `#5CB6D9` | Informação e segurança |
| `--border` | `200 38% 19%` | `#1E3642` | Bordas e divisores |
| `--destructive` | `0 100% 71%` | `#FF6B6B` | Erros e ações destrutivas |

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
