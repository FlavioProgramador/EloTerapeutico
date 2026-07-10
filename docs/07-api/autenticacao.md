# Autenticação da API

## Bearer JWT

Envie o access token:

```http
Authorization: Bearer <access-token>
```

A autenticação global usa `SafeJWTAuthentication`. Access e refresh possuem tempos configuráveis; refresh é rotacionado e invalidado após mudança de senha.

## Fluxo

1. `POST /auth/login/` retorna tokens;
2. cliente usa access nas rotas protegidas;
3. ao expirar, envia refresh para `/auth/token/refresh/`;
4. recebe novo access e normalmente novo refresh;
5. logout coloca refresh na blacklist.

## Erros

- access ausente/inválido: 401;
- refresh inválido, expirado, revogado ou incompatível com a senha: 401/erro de token;
- logout sem refresh ou com token inválido: 400.

## Segurança

- use HTTPS;
- não inclua tokens em query string;
- não registre Authorization;
- limite a vida do access;
- revogue sessões após incidente;
- o frontend atual precisa evoluir para cookies HttpOnly definidos pelo servidor ou arquitetura equivalente.

[Voltar](README.md)
