# Endpoints — Autenticação e usuários

## POST `/api/v1/auth/register/`

Cadastro público. Valida confirmação e força da senha. Retorna mensagem, tokens e perfil. Rate limit 10/minuto quando ativo.

## POST `/api/v1/auth/login/`

Payload: `email`, `password`. Retorna `access`, `refresh`, `user`. Mensagem de falha é genérica. Rate limit 5/minuto.

## POST `/api/v1/auth/logout/`

JWT obrigatório. Payload: `refresh`. Confirma propriedade e aplica blacklist.

## POST `/api/v1/auth/token/refresh/`

Payload: `refresh`. Valida usuário ativo e hash da senha, rotaciona e bloqueia token anterior.

## POST `/api/v1/auth/password/change/`

JWT. Campos `current_password`, `new_password`, `new_password_confirm`.

## POST `/api/v1/auth/password/reset/`

Público. Campo `email`. Sempre responde de forma genérica; rate limit 3/hora.

## POST `/api/v1/auth/password/reset/confirm/`

Campos `uidb64`, `token`, `new_password`, `new_password_confirm`.

## GET/PATCH `/api/v1/auth/me/`

Consulta/edita perfil próprio. Role e e-mail são somente leitura.

## `/api/v1/auth/working-hours/`

List/create e detail/update/delete de horários pertencentes ao usuário.

[Voltar à API](../README.md)
