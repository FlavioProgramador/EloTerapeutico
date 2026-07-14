# Módulo de autenticação

**Status: implementado.**

## Finalidade e atores

Autenticar usuários por e-mail e senha, emitir tokens, recuperar acesso e encerrar sessões. Atende terapeutas, secretárias e administradores.

## Entidades e dados

Usa `apps.users.User`, `OutstandingToken` e `BlacklistedToken` do Simple JWT. Campos relevantes: `email`, hash de senha, `is_active`, `failed_login_attempts`, `locked_until`, `last_login` e `role`.

## Regras de negócio

- e-mail é o identificador único;
- senha passa pelos validadores Django e tem mínimo configurado de oito caracteres;
- Argon2 é o primeiro hasher em ambientes normais;
- mensagem de login é genérica para usuário inexistente, bloqueado, inativo ou senha incorreta;
- usuário inexistente executa dummy hashing para reduzir diferença de tempo;
- cinco falhas consecutivas bloqueiam a conta por 30 minutos;
- login bem-sucedido zera falhas e bloqueio;
- access token dura 30 minutos por padrão;
- refresh dura sete dias, é rotacionado e o anterior entra em blacklist;
- o hash da senha é incluído na verificação de revogação, invalidando refresh após alteração;
- reset de senha responde sempre com mensagem genérica e usa token temporário do Django;
- rate limits: cadastro 10/minuto, login 5/minuto e solicitação de reset 3/hora em ambientes onde o rate limit está ativo.

## API

| Método | Rota | Autenticação | Uso |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register/` | Pública | Cadastro e emissão de tokens |
| POST | `/api/v1/auth/login/` | Pública | Login |
| POST | `/api/v1/auth/logout/` | JWT | Blacklist do refresh pertencente ao usuário |
| POST | `/api/v1/auth/token/refresh/` | Refresh | Rotação segura |
| POST | `/api/v1/auth/password/change/` | JWT | Troca autenticada |
| POST | `/api/v1/auth/password/reset/` | Pública | Solicitação anti-enumeração |
| POST | `/api/v1/auth/password/reset/confirm/` | Pública + token | Confirmação do reset |

Exemplo de login:

```json
{
  "email": "terapeuta@example.test",
  "password": "senha-ficticia-forte"
}
```

Resposta contém `access`, `refresh` e `user`. Tokens reais nunca devem aparecer em logs ou documentação.

## Frontend

- páginas de login, cadastro e recuperação;
- `AuthProvider` mantém perfil e sessão;
- interceptor Axios injeta access token e coordena refresh;
- redirecionamento aceita apenas caminho relativo local;
- logout tenta invalidar o refresh e sempre limpa estado local.

## Permissões

Endpoints públicos declaram `AllowAny`; demais usam `IsAuthenticated`. A role não é definida pelo cadastro público nem editável no serializer de perfil.

## Segurança e auditoria

Controles implementados: anti-enumeração, dummy hashing, bloqueio, rotação, blacklist, comparação segura no refresh e password validators. Risco residual: tokens ficam em cookies criados pelo JavaScript, sem `HttpOnly` e sem `secure` explícito no código cliente.

## Testes relacionados

- `apps/users/tests/test_auth.py`;
- `test_password_reset.py`;
- `test_logout_security.py`;
- regressões em `backend/apps/core/quality/`.

## Limitações

- não há MFA;
- envio de reset é síncrono;
- bloqueio depende do banco e não substitui proteção no proxy/WAF;
- cookies de autenticação devem ser redesenhados antes de produção com alto risco.

Implementação relacionada: `backend/apps/users/api/` e `frontend/src/contexts/auth.tsx`.

[Voltar aos módulos](../README.md)
