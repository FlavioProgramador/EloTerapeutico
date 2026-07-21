# Design System — Elo Terapêutico

## Direção visual

> **Acolhimento seguro:** confiança clínica com aparência tecnológica madura.

A interface deve transmitir profissionalismo, calma, segurança e clareza sem parecer fria ou produzida por um gerador genérico de dashboards.

Princípios:

- clareza antes de decoração;
- laranja quente como identidade principal, ação, seleção, foco e destaque editorial;
- neutros quentes para fundos, textos, superfícies e bordas;
- carvão quente para navegação lateral e áreas escuras;
- verde exclusivamente para sucesso, confirmação e disponibilidade positiva;
- nenhuma área estrutural, institucional ou decorativa deve usar verde como cor dominante;
- bordas finas e sombras discretas;
- nenhuma informação clínica deve depender somente da cor;
- dados pessoais e clínicos devem ser minimizados por padrão.

---

## Paleta semântica

A base histórica está em `frontend/src/app/globals.css`. A direção visual vigente é aplicada em `frontend/src/app/orange-theme.css`, importado depois de `globals.css` em `frontend/src/app/layout.tsx`. Componentes devem usar tokens como `bg-card`, `text-foreground`, `bg-primary` e `border-border`, sem repetir valores HSL ou HEX diretamente.

### Tema claro vigente

| Token | HSL | Uso |
|---|---:|---|
| `--background` | `30 38% 97%` | Fundo geral neutro quente |
| `--foreground` | `24 18% 15%` | Texto padrão carvão quente |
| `--card` | `0 0% 100%` | Cards e painéis |
| `--primary` | `27 86% 54%` | Cor principal laranja |
| `--primary-hover` | `24 86% 48%` | Hover da ação principal |
| `--primary-active` | `22 82% 42%` | Clique da ação principal |
| `--primary-soft` | `28 92% 94%` | Destaque, seleção e foco suave |
| `--secondary` | `30 55% 93%` | Ações e superfícies secundárias |
| `--border` | `30 22% 86%` | Bordas padrão |
| `--success` | `149 32% 36%` | Sucesso e confirmação somente |
| `--warning` | `31 67% 55%` | Atenção não bloqueante |
| `--info` | `199 89% 48%` | Informação contextual |
| `--danger` | `15 59% 45%` | Erro e ação destrutiva |
| `--sidebar` | `24 18% 12%` | Navegação em carvão quente |
| `--sidebar-active` | `27 86% 58%` | Item ativo da navegação |

### Tema escuro vigente

| Token | HSL | Uso |
|---|---:|---|
| `--background` | `24 16% 9%` | Fundo geral |
| `--foreground` | `30 28% 95%` | Texto principal |
| `--card` | `24 14% 13%` | Cards e painéis |
| `--primary` | `27 90% 59%` | Ação principal laranja |
| `--primary-soft` | `25 68% 15%` | Seleção suave laranja |
| `--secondary` | `24 12% 16%` | Ações secundárias |
| `--border` | `24 10% 21%` | Bordas e divisores |
| `--success` | `149 32% 42%` | Sucesso somente |
| `--danger` | `15 67% 55%` | Erro e destrutivo |
| `--sidebar` | `24 18% 6%` | Navegação lateral carvão |
| `--sidebar-active` | `27 90% 59%` | Item ativo laranja |

### Regras de estado

- `primary`: ação principal, seleção, link importante, navegação ativa, foco e destaque de marca;
- `success`: operação concluída, pagamento recebido, conexão validada ou disponibilidade confirmada;
- `warning`: pendência ou atenção não bloqueante;
- `info`: ajuda e informação contextual;
- `danger` ou `destructive`: erro, remoção, cancelamento e bloqueio.

Não use verde como fundo institucional, sidebar, destaque de marca, CTA ou decoração. Não use `primary` para erro, alerta ou indisponibilidade. Estados devem combinar cor, ícone e texto.

### Compatibilidade legada

Classes antigas das famílias `green`, `emerald`, `teal` e `lime` são redirecionadas para a escala laranja em `orange-theme.css`. Isso evita que componentes antigos reintroduzam verde estrutural. Novos componentes devem usar tokens semânticos diretamente.

---

## Landing page

A landing page segue a mesma identidade laranja do produto. Áreas editoriais escuras usam carvão quente, não verde. Tons antes chamados de `sage` permanecem apenas como nomes técnicos legados e são convertidos para variações quentes de laranja.

Obrigatório:

- CTA principal laranja;
- links de destaque laranja;
- foco e seleção laranja;
- fundos claros em branco ou neutros quentes;
- áreas escuras em carvão quente;
- verde somente para confirmação positiva real;
- texto de botão principal com `primary-foreground`.

---

## Autenticação

As páginas de login e cadastro preservam as ilustrações originais do produto:

- login: `/login_illustration.svg`;
- cadastro: `/register_illustration.svg`.

Regras:

- as imagens devem permanecer visíveis em desktop;
- não substituir as ilustrações por blocos verdes, painéis genéricos ou fundos chapados;
- sobreposições devem usar laranja suave e transparência moderada;
- cards sobre as imagens usam branco ou superfície neutra com contraste adequado;
- no mobile, a coluna ilustrada pode ser ocultada para priorizar o formulário;
- o fluxo seguro via BFF, cookies HttpOnly e mensagens públicas sanitizadas não pode ser alterado por mudanças visuais.

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
- `rounded-full`: avatar, status e progresso circular;
- `rounded-2xl` e `rounded-3xl` podem ser usados em páginas públicas e autenticação, mas devem ser evitados em interfaces operacionais densas.

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
- retorno de verde como cor estrutural ou institucional;
- remoção das ilustrações originais de login e cadastro;
- cores literais em componentes;
- texto relevante menor que 12px;
- supressão global do console;
- credenciais preenchidas ou retornadas.

Ao editar uma tela antiga:

1. substitua cores literais por tokens;
2. valide tema claro e escuro;
3. verifique que o laranja continua como destaque principal;
4. aplique minimização de dados;
5. revise estados loading, vazio e erro;
6. teste teclado, foco, hover, disabled e erro;
7. remova a compatibilidade antiga quando não houver consumidores.
