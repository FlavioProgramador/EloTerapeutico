# Headers, cookies e armazenamento privado

## Settings de produção

- `SECURE_SSL_REDIRECT=True`;
- HSTS por um ano, subdomínios e preload;
- `nosniff`;
- referrer policy same-origin;
- COOP same-origin;
- `X_FRAME_OPTIONS=DENY`;
- session e CSRF cookies do Django seguros;
- CORS sem wildcard e origens obrigatórias.

## Sessão JWT pelo BFF

O navegador não recebe nem lê access token ou refresh token. O Next.js atua como Backend for Frontend:

```text
Navegador
→ Route Handler /api/auth ou /api/backend
→ Authorization Bearer adicionado no servidor
→ Django REST Framework
```

Cookies usados pelo BFF:

| Cookie | Acesso JavaScript | Finalidade |
| --- | --- | --- |
| `elo_access` | Não (`HttpOnly`) | Access token de curta duração |
| `elo_refresh` | Não (`HttpOnly`) | Refresh token rotativo |
| `elo_csrf` | Sim | Double-submit token para requisições mutáveis; não é credencial de autenticação |

Regras aplicadas:

- `HttpOnly` para access e refresh;
- `Secure` em produção;
- `SameSite=Lax`;
- `Path=/`;
- duração configurável;
- respostas de login, cadastro e refresh são sanitizadas;
- `Authorization` é adicionado somente no servidor Next.js;
- requests `POST`, `PUT`, `PATCH` e `DELETE` autenticados exigem `X-CSRF-Token`;
- cookie e header CSRF são comparados em tempo constante;
- endpoints públicos de autenticação validam `Origin` e `Sec-Fetch-Site`;
- o proxy genérico bloqueia login, refresh e logout;
- nenhuma credencial é persistida em `localStorage`, `sessionStorage` ou IndexedDB;
- logout remove os três cookies com `Max-Age=0` e data expirada.

A presença do cookie no middleware serve apenas para navegação. Validade da sessão, role, tenant, assinatura e permissão de objeto são confirmados pelo Django.

### Falhas do gateway

Falhas de conexão, timeout, DNS, payload inválido ou exceção inesperada não podem expor URL interna, mensagem original, causa, stack ou corpo do upstream.

Contrato público:

```json
{
  "error": {
    "code": "AUTH_GATEWAY_UNAVAILABLE",
    "message": "O serviço de autenticação está temporariamente indisponível."
  },
  "request_id": "identificador-seguro"
}
```

O log interno contém somente evento, request ID sanitizado e tipo da exceção. Headers, cookies, tokens, credenciais e payloads completos são proibidos.

### Variáveis do frontend

Consulte `frontend/.env.example`:

- `BACKEND_API_URL`: URL interna do Django acessível pelo processo Next.js;
- `AUTH_ACCESS_COOKIE_MAX_AGE`;
- `AUTH_REFRESH_COOKIE_MAX_AGE`.

No Docker, `BACKEND_API_URL` deve apontar para o nome interno do serviço, não para `localhost` do navegador.

### Validação automatizada

```bash
cd frontend
npm run test:auth
```

O workflow `.github/workflows/auth-e2e.yml` usa PostgreSQL e aplicações reais para validar cookies HttpOnly, CSRF, rotação, blacklist, logout e resposta segura de gateway. Traces e screenshots são publicados somente em falha; vídeos, logs de cookies e dumps de banco não são artefatos.

### Risco residual

Cookies HttpOnly reduzem o impacto de exfiltração de token por XSS, mas não eliminam ações em nome do usuário. CSP forte, escaping, sanitização, dependências atualizadas e CSRF continuam obrigatórios.

## Storage

Em produção, Azure Blob é usado quando há connection string. Configure:

- container privado;
- URLs temporárias curtas;
- identidade gerenciada ou segredo protegido;
- bloqueio de acesso público;
- firewall/private endpoint quando aplicável;
- versionamento/soft delete conforme política;
- logging e alertas;
- `PRIVATE_MEDIA_STORAGE_REQUIRED=True`.

### Bloqueador

Filesystem local em serviço efêmero pode perder arquivos ou divergir entre réplicas. Não use com dados clínicos reais.

[Voltar](README.md)
