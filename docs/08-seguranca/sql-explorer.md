# SQL Explorer administrativo

## Situação

O SQL Explorer é uma ferramenta excepcional de suporte técnico. Ele fica **desabilitado por padrão**, não é registrado nas URLs quando desligado e é **proibido nos settings de produção**.

A preferência operacional continua sendo consultar métricas, health checks, relatórios administrativos e observabilidade estruturada. SQL arbitrário não deve fazer parte do fluxo comum do backoffice.

## Controles implementados

Quando a ferramenta é habilitada em um ambiente não produtivo autorizado, todos os controles abaixo são aplicados:

- usuário autenticado, ativo e superusuário;
- permissão Django explícita `core.use_sql_explorer` atribuída diretamente ou por grupo;
- uma única instrução por execução;
- apenas `SELECT` simples;
- bloqueio de CTEs, inclusive CTEs modificadoras;
- bloqueio de `EXPLAIN` e `EXPLAIN ANALYZE`;
- bloqueio de DML, DDL e palavras-chave administrativas;
- bloqueio de subconsultas e funções administrativas perigosas;
- allowlist explícita de tabelas;
- transação `READ ONLY` no PostgreSQL;
- `statement_timeout` local;
- limite máximo de linhas;
- rollback ao final da transação;
- erros internos sanitizados;
- auditoria por hash SHA-256 da consulta, status e justificativa;
- ausência de histórico de consultas no navegador;
- ausência de exportação CSV na ferramenta;
- schema/autocomplete limitado às tabelas autorizadas.

A consulta completa não é persistida pela aplicação nem registrada nos logs. A justificativa também não deve conter nome, CPF, e-mail, prontuário ou outro dado pessoal.

## Configuração

Variáveis disponíveis somente para desenvolvimento/homologação controlados:

```env
ADMIN_SQL_EXPLORER_ENABLED=False
ADMIN_SQL_EXPLORER_DATABASE_ALIAS=default
ADMIN_SQL_EXPLORER_MAX_ROWS=100
ADMIN_SQL_EXPLORER_TIMEOUT_MS=2000
ADMIN_SQL_EXPLORER_ALLOWED_TABLES=django_migrations
```

### Regras

- mantenha `ADMIN_SQL_EXPLORER_ENABLED=False` por padrão;
- use a menor allowlist possível;
- não autorize tabelas clínicas, de autenticação, billing, auditoria ou segredos sem uma necessidade formalmente aprovada;
- limite o acesso ao período estritamente necessário;
- remova a permissão após o atendimento;
- não compartilhe resultados por canais não autorizados;
- nunca habilite a variável nos settings de produção.

Se `ADMIN_SQL_EXPLORER_ENABLED=True` for fornecido ao ambiente de produção, a aplicação falha na inicialização com `ImproperlyConfigured`.

## Permissão explícita

A migration do app `core` cria a permissão:

```text
core.use_sql_explorer
```

A permissão pode ser atribuída pelo Django Admin a um grupo administrativo temporário ou diretamente ao superusuário autorizado. Ser superusuário, sozinho, não é suficiente: o código exige uma atribuição explícita real.

## Banco dedicado read-only

Mesmo com a transação read-only aplicada pela aplicação, ambientes de homologação críticos devem configurar um alias de banco com usuário PostgreSQL estritamente read-only e apontar `ADMIN_SQL_EXPLORER_DATABASE_ALIAS` para esse alias.

Exemplo conceitual de privilégios, a ser adaptado pela equipe de infraestrutura:

```sql
CREATE ROLE elo_inspector LOGIN PASSWORD '<segredo-gerenciado>';
GRANT CONNECT ON DATABASE <banco_homologacao> TO elo_inspector;
GRANT USAGE ON SCHEMA public TO elo_inspector;
GRANT SELECT ON TABLE django_migrations TO elo_inspector;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM elo_inspector;
```

Não versionar a senha e não reutilizar o usuário principal da aplicação.

## Auditoria

Para cada tentativa autorizada, o registro contém somente:

- ator;
- horário;
- IP confiável quando disponível;
- user agent minimizado;
- status (`concluida`, `bloqueada`, `erro_banco` ou `erro_interno`);
- hash SHA-256 da consulta;
- justificativa sanitizada.

Tentativas de acesso autenticadas sem permissão também são registradas. A auditoria não inclui a consulta completa nem conteúdo clínico.

## Testes

A suíte `apps/core/tests/test_admin_sql_security.py` cobre:

- feature flag;
- acesso anônimo, usuário comum, staff e superusuário sem permissão;
- permissão explícita;
- comandos de escrita;
- CTEs;
- múltiplas instruções;
- `EXPLAIN ANALYZE`;
- subconsultas;
- allowlist;
- limite de linhas;
- justificativa;
- sanitização de erro;
- auditoria por hash;
- schema restrito;
- configuração read-only e timeout do PostgreSQL.

## Rollback

O rollback funcional consiste em manter `ADMIN_SQL_EXPLORER_ENABLED=False`. Para remover a implementação, reverta o Pull Request. A migration adiciona apenas estado de ContentType/permissão para um modelo não gerenciado; nenhuma tabela de domínio é criada e nenhum dado clínico é alterado.
