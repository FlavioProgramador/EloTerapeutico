# ADR — Multi-tenancy por organização explícita

## Status

Aceita.

## Contexto

O sistema legado isolava grande parte dos dados pelo terapeuta responsável. Esse modelo não atende adequadamente:

- clínicas com vários profissionais;
- usuários com papéis diferentes por clínica;
- recepção e financeiro sem acesso clínico;
- um profissional atuando em mais de uma organização;
- crescimento de consultório individual para equipe;
- workers, relatórios, arquivos e auditoria com escopo explícito.

## Decisão

Adotar multi-tenancy lógico por coluna, usando `Organization` como raiz do tenant e `OrganizationMembership` como vínculo de acesso.

Recursos operacionais persistem `organization_id`. A organização ativa é resolvida após autenticação por `X-Organization-ID` e membership ativa.

O sistema não utiliza schema separado por tenant nesta fase.

## Consequências positivas

- mesma arquitetura para profissional individual e clínica;
- filtros e índices previsíveis;
- possibilidade de um usuário participar de múltiplas organizações;
- papéis específicos por tenant;
- migração incremental sem recriar IDs;
- compatibilidade com PostgreSQL, Celery e storage atuais.

## Consequências e riscos

- toda query tenant-owned precisa de filtro explícito;
- tasks e integrações devem transportar `organization_id`;
- relações cruzadas precisam de validação de domínio;
- testes devem criar pelo menos dois tenants;
- relatórios e caches antigos precisam ser revisados;
- bypass administrativo deve ser explícito e auditado.

## Alternativas rejeitadas

### Continuar isolando por terapeuta

Rejeitada porque não representa recepção, financeiro, equipes, unidades ou profissionais com múltiplos vínculos.

### Um banco por clínica

Rejeitada para esta fase por custo operacional, complexidade de migrations e inviabilidade para clientes individuais pequenos.

### Um schema PostgreSQL por tenant

Rejeitada nesta fase pela complexidade com migrations, Celery, conexões e ferramentas administrativas. Pode ser reavaliada para requisitos empresariais futuros.

### Manager global baseado em thread-local

Rejeitado porque esconder o tenant pode causar consultas imprevisíveis em migrations, admin, workers e testes. Preferimos parâmetros explícitos em selectors e services.

## Migração

A mudança deve seguir `expand -> backfill -> validate -> contract`. Nenhum campo tenant-owned é tornado obrigatório antes da auditoria de integridade.

## Billing

Planos permanecem globais. Temporariamente, a assinatura é resolvida pelo owner da organização por uma camada de adaptação, sem criar cobrança por membro.
