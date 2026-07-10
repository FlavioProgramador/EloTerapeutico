# Casos de uso — Autenticação

# UC-AUTH-001 — Autenticar usuário

## Objetivo
Permitir acesso com e-mail e senha.

## Atores
Usuário cadastrado.

## Pré-condições
Conta ativa e não bloqueada.

## Permissões necessárias
Endpoint público, sujeito a rate limit.

## Gatilho
Envio do formulário de login.

## Fluxo principal
1. Frontend envia e-mail e senha.
2. Backend localiza a conta e valida o hash.
3. Falhas anteriores são zeradas.
4. API emite access e refresh tokens e retorna o perfil.
5. Frontend armazena tokens e redireciona ao destino local seguro.

## Fluxos alternativos
### A1 — Conta inexistente
Backend executa dummy hashing e retorna mensagem genérica.

### A2 — Senha inválida
A tentativa é incrementada; na quinta falha a conta é bloqueada por 30 minutos.

## Exceções
### E1 — Rate limit
A requisição é bloqueada pelo mecanismo configurado.

## Pós-condições
Sessão cliente criada; refresh pode ser rotacionado depois.

## Dados envolvidos
E-mail, senha em trânsito, hash, falhas, bloqueio e tokens.

## Eventos de auditoria
Não foi comprovado AuditLog clínico específico para login; logs não devem conter credenciais.

## Regras de segurança
TLS obrigatório; mensagem genérica; tokens não devem ser logados.

## Endpoints relacionados
`POST /api/v1/auth/login/`.

## Componentes relacionados
`frontend/src/app/login/page.tsx`, `AuthProvider` e cliente Axios.

## Testes relacionados
`apps/users/tests/test_auth.py`.

## Status de implementação
Implementado.

---

# UC-AUTH-002 — Redefinir senha

## Objetivo
Recuperar acesso sem revelar se o e-mail existe.

## Atores
Usuário ou pessoa solicitante.

## Pré-condições
SMTP configurado para entrega real; conta ativa para envio.

## Fluxo principal
1. Solicitante informa e-mail.
2. API responde sempre com mensagem genérica.
3. Para conta ativa, backend gera UID e token temporário.
4. E-mail contém link do frontend.
5. Usuário informa nova senha e confirmação.
6. Backend valida token e força da senha.
7. Senha é atualizada; refresh anterior se torna inválido pela verificação do hash.

## Exceções
Token inválido/expirado ou senha fraca retornam erro de validação.

## Dados envolvidos
E-mail, UID, token temporário e nova senha.

## Regras de segurança
Rate limit 3/hora; URL do frontend configurada; não registrar token; resposta anti-enumeração.

## Endpoints relacionados
`POST /auth/password/reset/` e `/auth/password/reset/confirm/`.

## Status de implementação
Implementado; entrega depende de SMTP.

---

# UC-AUTH-003 — Encerrar sessão

## Fluxo principal
1. Frontend envia o refresh atual autenticado.
2. Backend confirma que o token pertence ao usuário.
3. Refresh entra na blacklist.
4. Frontend remove tokens e role local.

## Exceções
Token ausente, inválido ou já expirado retorna 400; o frontend ainda limpa o estado local.

## Status de implementação
Implementado.

[Voltar](README.md)
