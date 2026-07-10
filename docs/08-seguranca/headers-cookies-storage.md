# Headers, cookies e armazenamento privado

## Settings de produção

- `SECURE_SSL_REDIRECT=True`;
- HSTS por um ano, subdomínios e preload;
- `nosniff`;
- referrer policy same-origin;
- COOP same-origin;
- `X_FRAME_OPTIONS=DENY`;
- session e CSRF cookies Secure, HttpOnly e SameSite Lax;
- CORS sem wildcard e origens obrigatórias.

## Cookies JWT do frontend

Os cookies Django acima não protegem automaticamente `auth_token`, `auth_refresh_token` e `auth_role`, pois eles são criados no navegador com `cookies-next`. JavaScript não pode marcar cookie como HttpOnly.

### Recomendação

Migrar para uma destas arquiteturas, após threat modeling:

1. backend/BFF define access/refresh em cookies HttpOnly, Secure e SameSite adequados;
2. sessão server-side com CSRF robusto;
3. access token apenas em memória e refresh HttpOnly com rotação.

Definir CSP forte e remover XSS continua necessário.

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
