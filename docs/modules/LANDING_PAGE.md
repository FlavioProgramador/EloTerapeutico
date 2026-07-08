# Landing page do Elo Terapêutico

A página inicial utiliza componentes independentes dentro de `frontend/src/features/landing` e mantém a identidade visual do produto em verde-petróleo, creme e verde-sálvia.

## Estrutura atual

- `landing-page.tsx`: composição e ordem narrativa das seções.
- `site-header.tsx`: navegação fixa, menu móvel e acesso rápido.
- `hero.tsx`: composição principal preservada com imagem, proposta de valor e CTAs.
- `benefit-rail.tsx`: faixa de diferenciais logo após o hero.
- `problem-section.tsx`: problema resolvido em mapa visual assimétrico.
- `product-stage.tsx`: demonstração interativa de dashboard, agenda, prontuários e financeiro.
- `journey.tsx`: timeline do fluxo de utilização.
- `module-stories.tsx`: apresentação aprofundada dos módulos em composições alternadas.
- `value-section.tsx`: comparação entre controles fragmentados e fluxo conectado.
- `trust-section.tsx`: segurança, permissões e rastreabilidade.
- `faq.tsx`: perguntas frequentes com `details` e `summary` nativos.
- `final-cta.tsx`: chamada final para cadastro.
- `site-footer.tsx`: identidade e links para rotas e seções existentes.
- `content.ts`: conteúdo compartilhado e tipado.
- `motion.tsx`: animações discretas com suporte a redução de movimento.
- `styles/`: arquivos separados por responsabilidade visual.

## Decisões visuais

- O hero mantém a composição aprovada: texto forte à esquerda, imagem acolhedora à direita e cartão flutuante.
- As seções posteriores evitam a repetição de grades de cards.
- Mockups são construídos com componentes da interface e identificados como demonstrativos.
- Timeline, mapas de conexão, comparação visual, órbitas e sobreposições criam ritmos diferentes sem quebrar o design system.
- Não são utilizados depoimentos, clientes, percentuais ou resultados sem fonte real.
- Não são anunciadas funcionalidades que não existem no projeto.

## Acessibilidade e desempenho

- Navegação por teclado e foco visível.
- Estrutura semântica de cabeçalho, seções, navegação e rodapé.
- Abas com papéis e atributos ARIA.
- FAQ com elementos nativos acessíveis.
- Animações respeitam `prefers-reduced-motion`.
- Nenhuma dependência nova foi adicionada.

## Validação

No diretório `frontend`, execute:

```bash
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

Revise também o comportamento em larguras de 320 px, 768 px, 1280 px e 1920 px, além do menu móvel, das abas e do FAQ.
