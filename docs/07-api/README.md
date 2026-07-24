# 07 — API

A API principal usa o prefixo `/api/v1/` e é documentada por `drf-spectacular`. O schema é contrato técnico e deve ser validado contra serializers, permissions, filtros e responses reais.

## Documentação e health

| Recurso | Rota |
| --- | --- |
| OpenAPI schema | `/api/schema/` |
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| Health legado de usuários | `/api/health/` |
| Liveness | `/health/live/` |
| Readiness | `/health/ready/` |
| Django Admin | `/admin/` |

## Prefixos versionados

| Domínio | Prefixo |
| --- | --- |
| Autenticação e usuários | `/api/v1/auth/` |
| Organizações | `/api/v1/organizations/` |
| Aceite público de convite | `/api/v1/organization-invitations/accept/` |
| Pacientes | `/api/v1/patients/` |
| Prontuário | `/api/v1/records/` |
| Agenda, scheduling e telemedicina | `/api/v1/scheduling/` |
| Financeiro clínico | `/api/v1/finances/` |
| Documentos | `/api/v1/documents/` |
| Relatórios | `/api/v1/reports/` |
| Formulários | `/api/v1/forms/` |
| Billing SaaS | `/api/v1/billing/` |
| Comunicações | `/api/v1/communications/` |
| Ações públicas de comunicações | `/api/v1/public/communications/` |

Uma rota legada de Billing pode ser registrada em `/api/billing/` quando a feature de compatibilidade estiver habilitada. Não use a rota legada em novos consumidores.

## Autenticação e BFF

O navegador consome, em regra, o gateway Next.js em `/api/backend/`. O BFF:

- mantém access e refresh tokens em cookies `HttpOnly`;
- aplica proteção CSRF para métodos mutáveis;
- remove `Authorization` criado no navegador;
- adiciona o Bearer token somente no servidor;
- coordena refresh de sessão;
- sanitiza falhas do upstream.

O frontend não deve contornar o BFF com um cliente paralelo para endpoints autenticados.

## Tenant

Em produção, requisições tenant-aware usam organização ativa e podem encaminhar:

```text
X-Organization-ID: <uuid>
```

O ID não concede acesso. O backend valida autenticação, membership ativa, status da organização, papel, ownership e entitlement.

## Convenções

- JSON como formato principal;
- autenticação Bearer somente entre BFF e backend nos fluxos web;
- paginação padrão em endpoints de coleção;
- filtros por `django-filter`;
- busca e ordenação quando declaradas;
- erros normalizados pelo exception handler do Core;
- mensagens públicas sem stack trace, URL interna, segredo ou causa sensível;
- `Idempotency-Key` em operações críticas que suportam repetição segura;
- endpoints públicos com rate limit, tokens temporários e respostas genéricas;
- versionamento explícito em `/api/v1/`.

## Paginação

A paginação padrão é configurada por `apps.core.api.pagination.StandardResultsPagination`, com page size padrão `20`. Endpoints podem restringir ou especializar esse comportamento.

## OpenAPI

Valide localmente:

```bash
cd backend
python manage.py spectacular --file schema.yml --validate
```

O schema não deve conter dados reais, credenciais, tokens ou exemplos clínicos identificáveis.

## Guias

- [Autenticação](autenticacao.md)
- [Autorização](autorizacao.md)
- [Erros](erros.md)
- [Scheduling](endpoints/scheduling.md)
- [Telemedicina](endpoints/telemedicina.md)
- [Financeiro](endpoints/finances.md)
- [Billing](endpoints/billing.md)

Documentação de cada módulo também descreve seus endpoints e limitações.

[Voltar ao portal](../README.md)
