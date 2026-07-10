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
- reset com token Django e timeout configurável;
- rate limit em produção.

### Pendente/recomendado

- MFA para staff e contas privilegiadas;
- gestão de sessões visível ao usuário;
- revogação administrativa de todas as sessões;
- detecção de login anômalo;
- entrega assíncrona de e-mail;
- cookies HttpOnly/Secure definidos pelo servidor.

## Autorização

### Implementado

- `IsAuthenticated` global;
- permission classes específicas;
- filtros por usuário/terapeuta;
- object permissions;
- codenames explícitos para conteúdo confidencial;
- role readonly no perfil;
- bloqueio de rotas clínicas para secretária na interface;
- permissões Django no admin.

### Regras obrigatórias

- nunca confiar em `auth_role` do cookie;
- nunca usar apenas esconder botão como autorização;
- filtrar queryset antes de buscar objeto;
- testar leitura, escrita, exportação e download separadamente;
- não conceder acesso confidencial só por `is_superuser` na lógica de records;
- validar propriedade de refresh, paciente, consulta, documento, pagamento e job.

## Multi-tenancy

A autorização atual não constitui multi-tenancy formal. Antes de equipes/clínicas, criar tenant explícito, memberships, papéis por tenant, constraints, índices, storage prefix e testes de isolamento.

[Voltar](README.md)
