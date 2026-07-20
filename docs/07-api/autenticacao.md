# Autenticação da API

## Arquitetura BFF

O navegador não recebe JWTs no corpo nem os lê por JavaScript. O Next.js atua como Backend for Frontend e mantém access/refresh em cookies `HttpOnly`:

```text
Navegador
   ↓ cookies HttpOnly + X-CSRF-Token
Route Handlers / BFF Next.js
   ↓ Authorization: Bearer adicionado no servidor
Django REST Framework
```

Chamadas diretas à API por clientes confiáveis continuam utilizando Bearer JWT:

```http
Authorization: Bearer <access-token>
```

A autenticação global usa `SubscriptionJWTAuthentication`, construída sobre o fluxo seguro do Simple JWT. Access e refresh possuem tempos configuráveis; refresh é rotacionado, colocado em blacklist quando substituído e invalidado após mudança de senha.

## Fluxo no navegador

1. `POST /api/auth/login` encaminha credenciais ao Django;
2. o BFF remove os tokens do payload público;
3. access e refresh são definidos em cookies `HttpOnly`, `SameSite=Lax` e `Secure` em produção;
4. `elo_csrf` permanece acessível ao navegador somente para o padrão double-submit;
5. operações mutáveis enviam `X-CSRF-Token` com o mesmo valor do cookie;
6. `POST /api/auth/refresh` lê o refresh somente no servidor e rotaciona ambos os cookies;
7. `POST /api/auth/logout` revoga a sessão e remove access, refresh e CSRF;
8. falhas do upstream retornam mensagem genérica e `request_id`, sem URL, stack ou causa interna.

## Fluxo para clientes de API

1. `POST /auth/login/` retorna tokens ao cliente autorizado;
2. o cliente usa access nas rotas protegidas;
3. ao expirar, envia refresh para `/auth/token/refresh/`;
4. recebe novo access e, com rotação habilitada, novo refresh;
5. logout coloca refresh na blacklist.

Nunca utilizar os endpoints diretos como atalho no frontend web.

## CSRF e origem

- `POST`, `PUT`, `PATCH` e `DELETE` autenticados exigem double-submit CSRF;
- cookie e header são comparados em tempo constante;
- `Origin` explícito deve coincidir com a origem da aplicação;
- sem `Origin`, somente contextos `same-origin`, `same-site`, `none` ou ausência controlada de `Sec-Fetch-Site` são aceitos;
- login/cadastro validam origem mesmo antes de existir sessão;
- refresh e logout limpam cookies quando a sessão é inválida.

## Erros

- access ausente/inválido: `401`;
- refresh ausente, expirado ou revogado: `401` e limpeza da sessão local;
- CSRF ausente/divergente: `403`;
- origem não permitida: `403`;
- gateway de autenticação indisponível: `502` com contrato público sanitizado;
- logout sem refresh: resposta idempotente controlada e cookies removidos.

## Testes

Testes unitários do frontend:

```bash
cd frontend
npm run test:auth
```

Testes E2E com aplicação, Django e PostgreSQL ativos:

```bash
cd frontend/e2e
npm install
npx playwright install chromium
npm run test:auth
```

No GitHub Actions, `.github/workflows/auth-e2e.yml` provisiona PostgreSQL, cria somente usuário sintético, inicia backend/frontend e cobre:

- cookies HttpOnly;
- ausência de JWT em storage e payload;
- CSRF ausente, divergente e origem externa;
- rotação de refresh;
- logout e blacklist;
- indisponibilidade do gateway sem vazamento interno.

## Segurança

- use HTTPS;
- não inclua tokens em query string;
- não registre `Authorization`, cookies ou payloads de token;
- limite a vida do access;
- revogue sessões após incidente;
- não envie artefatos E2E contendo cookies ou credenciais;
- autorização de objeto e tenant permanece obrigatória no Django.

[Voltar](README.md)
