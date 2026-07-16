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
→ Django REST Framework
```

Cookies usados pelo BFF:

| Cookie | Acesso JavaScript | Finalidade |
| --- | --- | --- |
| `elo_access` | Não (`HttpOnly`) | access token de curta duração |
| `elo_refresh` | Não (`HttpOnly`) | refresh token rotativo |
| `elo_csrf` | Sim | double-submit token para requisições mutáveis |

Regras aplicadas:

- `HttpOnly` para access e refresh;
- `Secure` em produção;
- `SameSite=Lax`;
- `Path=/`;
- duração configurável;
- respostas de login, cadastro e refresh são sanitizadas;
- `Authorization` é adicionado somente no servidor Next.js;
- requests `POST`, `PUT`, `PATCH` e `DELETE` autenticados exigem `X-CSRF-Token`;
- endpoints públicos de autenticação validam `Origin` e `Sec-Fetch-Site`;
- o proxy genérico bloqueia login, refresh e logout;
- nenhuma credencial é persistida em `localStorage`.

A presença do cookie no middleware serve apenas para navegação. Validade da sessão, role, tenant, assinatura e permissão de objeto são confirmados pelo Django.

### Variáveis do frontend

Consulte `frontend/.env.example`:

- `BACKEND_API_URL`: URL interna do Django acessível pelo processo Next.js;
- `AUTH_ACCESS_COOKIE_MAX_AGE`;
- `AUTH_REFRESH_COOKIE_MAX_AGE`.

No Docker, `BACKEND_API_URL` deve apontar para o nome interno do serviço, não para `localhost` do navegador.

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
