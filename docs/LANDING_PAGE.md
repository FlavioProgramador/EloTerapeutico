# Landing page do Elo Terapêutico

A página inicial foi reorganizada em componentes independentes dentro de `frontend/src/features/landing`.

## Estrutura

- `landing-page.tsx`: composição das seções.
- `site-header.tsx`: navegação fixa e menu móvel.
- `hero.tsx`: proposta de valor e chamadas principais.
- `product-preview.tsx`: demonstração interativa dos módulos.
- `feature-grid.tsx`: funcionalidades reais da plataforma.
- `workflow.tsx`: fluxo de utilização.
- `modules.tsx`: detalhes de agenda, prontuários e financeiro.
- `security.tsx`: controles de segurança apresentados sem promessas absolutas.
- `faq.tsx`: perguntas frequentes com `details` e `summary` nativos.
- `final-cta.tsx`: chamada final para cadastro.
- `site-footer.tsx`: identidade e navegação institucional.
- `content.ts`: conteúdo centralizado e tipado.
- `motion.tsx`: animações sutis com suporte a redução de movimento.
- `styles/`: estilos específicos da landing page.

## Regras de conteúdo

- Não utilizar números, depoimentos, clientes ou resultados que não possuam fonte real.
- Identificar mockups e dados fictícios como demonstrativos.
- Apresentar como disponíveis somente módulos existentes no projeto.
- Evitar promessas absolutas de conformidade ou segurança.

## Validação

No diretório `frontend`, execute:

```bash
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

Revise também navegação por teclado, menu móvel, FAQ e comportamento em larguras de 320 px, 768 px, 1280 px e 1920 px.
