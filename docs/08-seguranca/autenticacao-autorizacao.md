# Autenticação e autorização

## Autenticação

### Implementado

- e-mail único;
- password validators;
- Argon2;
- mensagens genéricas;
- dummy hashing;
- bloqueio após cinco falhas por 30 minutos;
- JWT access/refresh;
- rotação e blacklist;
- refresh vinculado ao hash atual da senha;
- sessões persistidas e revogáveis por dispositivo;
- claim `sid` compartilhada entre access e refresh;
- proteção contra replay e refresh concorrente por lock transacional;
- logout do dispositivo atual;
- logout de todas as sessões;
- listagem e revogação de dispositivo pelo proprietário;
- invalidação de sessões após troca ou redefinição de senha;
- validação de sessão ativa em cada autenticação JWT;
- reset com token Django e timeout configurável;
- rate limit em produção;
- access e refresh armazenados pelo BFF em cookies HttpOnly;
- CSRF double-submit para operações mutáveis;
- validação de origem nos endpoints públicos de autenticação.

### Fluxo

```text
Login/cadastro no navegador
→ Route Handler Next.js
→ Django valida credenciais e cria AuthSession
→ Next.js remove tokens da resposta
→ Next.js define elo_access e elo_refresh como HttpOnly
→ navegador recebe somente dados não sensíveis
```

O proxy `/api/backend/*` lê o access token no servidor Next.js e adiciona o header `Authorization`. O JavaScript do navegador nunca lê access ou refresh.

### Compatibilidade

`AUTH_REQUIRE_SESSION_CLAIM` é desativado explicitamente em desenvolvimento e testes durante a transição de tokens legados. Na ausência desse override, tokens sem `sid` são rejeitados. Não habilite compatibilidade legada em produção após a migração.

### Pendente/recomendado

- MFA para staff e contas privilegiadas;
- interface de segurança para exibir e revogar sessões;
- detecção e notificação de login anômalo;
- confirmação de senha para ações críticas;
- entrega assíncrona de e-mail.

## Autorização

### Implementado

- `IsAuthenticated` global;
- permission classes específicas;
- filtros por usuário/terapeuta;
- object permissions;
- codenames explícitos para conteúdo confidencial;
- role readonly no perfil;
- permissões Django no admin;
- middleware Next.js limitado à navegação, sem decidir autorização por role.

### Regras obrigatórias

- nunca confiar em papel ou tenant informados pelo navegador;
- nunca usar apenas esconder botão como autorização;
- filtrar queryset antes de buscar objeto;
- testar leitura, escrita, exportação e download separadamente;
- não conceder acesso confidencial só por `is_superuser` na lógica de records;
- validar propriedade de refresh, sessão, paciente, consulta, documento, pagamento e job;
- retornar 404 quando apropriado para não revelar recursos de outro escopo.

## Multi-tenancy

A autorização atual não constitui multi-tenancy formal. Antes de equipes/clínicas, criar tenant explícito, memberships, papéis por tenant, constraints, índices, storage prefix e testes de isolamento.

[Voltar](README.md)
