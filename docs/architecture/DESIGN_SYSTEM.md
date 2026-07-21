# Design System — Elo Terapêutico

## Direção visual

> **Acolhimento seguro:** confiança clínica com aparência tecnológica madura.

A interface deve transmitir profissionalismo, calma, segurança e clareza sem parecer fria ou produzida por um gerador genérico de dashboards.

Princípios:

- clareza antes de decoração;
- laranja terroso para identidade principal, ações importantes, seleção e foco;
- verde escuro como apoio institucional e referência espacial;
- verde sálvia apenas para sucesso e confirmação;
- superfícies neutras com contraste progressivo;
- bordas finas e sombras discretas;
- nenhuma informação clínica deve depender somente da cor;
- dados pessoais e clínicos devem ser minimizados por padrão.

---

## Paleta semântica

A implementação oficial está em `frontend/src/app/globals.css`. Componentes devem usar tokens como `bg-card`, `text-foreground`, `bg-primary` e `border-border`, sem repetir valores HSL ou HEX diretamente.

### Tema claro

| Token | HSL | HEX aproximado | Uso |
|---|---:|---:|---|
| `--background` | `84 10% 95%` | `#EFF1EC` | Fundo geral do app |
| `--foreground` | `159 24% 11%` | `#15241E` | Texto padrão |
| `--card` | `0 0% 100%` | `#FFFFFF` | Cards e painéis |
| `--primary` | `31 67% 50%` | `#D98E3F` | Cor principal laranja |
| `--primary-hover` | `31 67% 43%` | `#B97633` | Hover da ação principal |
| `--primary-active` | `31 67% 38%` | `#A3682D` | Clique da ação principal |
| `--primary-soft` | `31 67% 95%` | `#FCF3EA` | Seleção e foco suave |
| `--secondary` | `142 24% 92%` | `#E7F0EA` | Ações secundárias |
| `--border` | `147 18% 88%` | `#DCE6E0` | Bordas padrão |
| `--success` | `149 32% 36%` | `#3E795C` | Sucesso e confirmação |
| `--warning` | `31 67% 55%` | `#E19A4B` | Atenção não bloqueante |
| `--info` | `199 89% 48%` | `#0EA5E9` | Informação contextual |
| `--danger` | `15 59% 45%` | `#B9502F` | Erro e ação destrutiva |
| `--sidebar` | `177 57% 15%` | `#103C39` | Navegação institucional |
| `--sidebar-active` | `31 67% 55%` | `#E19A4B` | Item ativo da navegação |

### Tema escuro

| Token | HSL | Uso |
|---|---:|---|
| `--background` | `220 15% 10%` | Fundo geral |
| `--foreground` | `220 10% 94%` | Texto principal |
| `--card` | `220 12% 14%` | Cards e painéis |
| `--primary` | `31 75% 55%` | Ação principal laranja |
| `--primary-soft` | `31 75% 15%` | Seleção suave |
| `--secondary` | `220 12% 12%` | Ações secundárias |
| `--border` | `220 10% 18%` | Bordas e divisores |
| `--success` | `149 32% 42%` | Sucesso |
| `--danger` | `15 67% 55%` | Erro e destrutivo |
| `--sidebar` | `220 18% 7%` | Navegação lateral |
| `--sidebar-active` | `31 75% 55%` | Item ativo |

### Regras de estado

- `primary`: ação principal, seleção, link importante e foco;
- `success`: operação concluída, pagamento recebido, conexão validada;
- `warning`: pendência ou atenção não bloqueante;
- `info`: ajuda e informação contextual;
- `danger` ou `destructive`: erro, remoção, cancelamento e bloqueio.

Não use `primary` para erro, alerta ou indisponibilidade. Estados devem combinar cor, ícone e texto.

---

## Landing page

A landing page preserva o verde escuro como apoio institucional em fundos e áreas editoriais, mas não redefine semanticamente a cor principal do produto.

Obrigatório:

- CTA principal laranja;
- links de destaque laranja;
- foco e seleção laranja;
- verde escuro apenas como fundo ou apoio;
- verde sálvia apenas como estado positivo;
- texto de botão principal com `primary-foreground`.

---

## Tipografia

### Produto autenticado

Fonte principal: `Outfit`, com fallback para `Inter`, `system-ui` e `sans-serif`.

### Landing page

- títulos institucionais: `Piazzolla`;
- corpo: `Work Sans`;
- métricas: `IBM Plex Mono`, somente quando o contexto exigir leitura numérica.

### Escala de referência

| Nível | Classe | Uso |
|---|---|---|
| Título de página | `text-2xl font-bold tracking-tight` | Nome da tela, 24px |
| Título secundário | `text-xl font-semibold` | Destaque importante, 20px |
| Título de seção | `text-base font-semibold` | Blocos principais, 16px |
| Título de card | `text-sm font-semibold` | Cards e painéis, 14px |
| Corpo | `text-sm` ou `text-base` | Conteúdo padrão, 14px ou 16px |
| Metadado | `text-xs text-muted-foreground` | Datas e apoio, 12px |
| Rótulo compacto | `text-xs font-semibold` | KPIs e tabelas densas, 12px |

Regras:

- conteúdo clínico: mínimo de 14px;
- leitura prolongada: mínimo de 16px;
- inputs em mobile: mínimo de 16px;
- informações de pacientes, erros e instruções: nunca abaixo de 12px;
- classes arbitrárias menores que 12px são proibidas em conteúdo relevante.

---

## Geometria e espaçamento

O sistema usa grid de 4px.

| Token | Valor | Uso |
|---|---:|---|
| `space-1` | 4px | Ajustes mínimos |
| `space-2` | 8px | Badges e ícones |
| `space-3` | 12px | Controles compactos |
| `space-4` | 16px | Padding padrão |
| `space-6` | 24px | Separação de grupos |
| `space-8` | 32px | Seções de página |

Raios:

- `rounded-md` ou `rounded-lg`: inputs e botões;
- `rounded-lg`: navegação;
- `rounded-xl`: cards, drawers e modais;
- `rounded-full`: avatar, status e progresso circular.

Evite `rounded-2xl` e `rounded-3xl` em interfaces operacionais.

---

## Componentes

### Botões

Variantes oficiais:

- `primary`: ação principal;
- `secondary`: ação de apoio;
- `outline`: ação neutra;
- `ghost`: baixa prioridade;
- `destructive`: ação irreversível.

O texto da ação principal usa `text-primary-foreground`, nunca `text-white` fixo. Ações destrutivas exigem confirmação clara.

### Inputs

Inputs usam `bg-background` ou `bg-card`, `border-input`, foco com `ring`, label associado, `aria-invalid`, `aria-describedby` e autocomplete adequado.

Credenciais existentes nunca são preenchidas novamente. A interface recebe apenas o estado de configuração.

### Cards

Cards usam `bg-card`, `text-card-foreground`, `border-border` e sombra mínima. Hover só existe quando o card é interativo.

### Badges

Badges representam estado com fundo suave, borda discreta, ícone ou texto e contraste legível. Badge não funciona como botão.

### Toasts e alertas

- sucesso: `success`;
- informação: `info`;
- atenção: `warning`;
- erro: `destructive`.

Toasts clínicos devem usar texto neutro e nunca incluir conteúdo de prontuário, nome de hipótese clínica ou outro dado sensível.

---

## Proteção de dados na interface

A interface aplica minimização por padrão.

Devem ser mascarados quando a exibição integral não for indispensável:

- CPF;
- telefone;
- e-mail;
- endereço;
- data de nascimento;
- tokens e identificadores de integração;
- links privados.

Utilitários oficiais ficam em `frontend/src/lib/privacy/masks.ts`.

Regras:

- CPF usa `masked_cpf` quando fornecido pela API;
- dados revelados não são persistidos em Web Storage;
- conteúdo clínico não aparece em URLs, toasts, logs ou notificações genéricas;
- links de telemedicina são ações, não texto exposto;
- nomes fictícios não podem ser fallback em produção;
- autorização definitiva permanece no backend.

---

## Mensagens públicas e erros

O frontend usa `frontend/src/lib/errors/public-error.ts`.

Somente são exibidas:

- mensagens mapeadas por código público conhecido;
- validações de campos presentes na allowlist;
- mensagens neutras por status HTTP.

É proibido renderizar diretamente:

- `response.data`;
- `error.message`;
- `last_error.message`;
- stack traces;
- nomes de exceptions;
- variáveis de ambiente;
- caminhos internos;
- detalhes de banco, filas, containers ou deploy;
- tokens ou credenciais.

Erros desconhecidos usam uma mensagem neutra e orientada à ação.

---

## Sessão e navegador

Preservar:

- tokens em cookies HttpOnly;
- BFF como fronteira do navegador;
- CSRF em métodos inseguros;
- backend como autoridade de permissão;
- React Query Devtools somente em desenvolvimento.

É proibido:

- armazenar tokens ou conteúdo clínico em `localStorage` ou `sessionStorage`;
- criar cliente HTTP paralelo que contorne o BFF;
- suprimir globalmente erros do console;
- usar role da interface como autorização definitiva.

---

## Acessibilidade

- contraste mínimo de 4.5:1 para texto normal;
- contraste mínimo de 3:1 para texto grande e componentes;
- foco visível em todos os controles;
- navegação por teclado;
- `aria-label` em botões somente com ícone;
- mensagens de erro com `role="alert"`;
- modais com `role="dialog"`, `aria-modal`, focus trap e retorno de foco;
- estados combinam texto, ícone e cor;
- respeito a `prefers-reduced-motion`.

---

## Testes estruturais

A suíte deve impedir regressões relacionadas a:

- mensagens técnicas visíveis;
- dados fictícios em produção;
- CPF completo na tela de paciente;
- renderização direta de erros internos;
- uso de Web Storage em fluxos sensíveis;
- cores literais em componentes;
- texto relevante menor que 12px;
- supressão global do console;
- credenciais preenchidas ou retornadas.

Ao editar uma tela antiga:

1. substitua cores literais por tokens;
2. valide tema claro e escuro;
3. aplique minimização de dados;
4. revise estados loading, vazio e erro;
5. teste teclado, foco, hover, disabled e erro;
6. remova a compatibilidade antiga quando não houver consumidores.
