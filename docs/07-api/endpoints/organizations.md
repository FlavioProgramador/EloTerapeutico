# API de organizações

Base: `/api/v1/organizations/`

Todas as rotas autenticadas aceitam `X-Organization-ID`. O header não concede acesso; o backend confirma membership ativa.

## Organizações

| Método | Rota | Descrição |
|---|---|---|
| GET | `/organizations/` | Lista organizações acessíveis |
| POST | `/organizations/` | Cria organização e membership owner |
| GET | `/organizations/{id}/` | Detalha organização permitida |
| PATCH | `/organizations/{id}/` | Atualiza dados institucionais |
| GET | `/organizations/context/` | Retorna organização/membership ativa e opções |
| POST | `/organizations/{id}/activate/` | Valida e ativa o contexto solicitado |

## Membros

| Método | Rota | Descrição |
|---|---|---|
| GET | `/organizations/{id}/members/` | Lista memberships |
| POST | `/organizations/{id}/members/` | Cria vínculo administrativo permitido |
| GET | `/organizations/{id}/members/{membership_id}/` | Detalha membro |
| PATCH | `/organizations/{id}/members/{membership_id}/` | Altera papel ou status |
| DELETE | `/organizations/{id}/members/{membership_id}/` | Revoga membership |

O backend impede remover o último owner ativo e limita ações exclusivas de propriedade.

## Convites

| Método | Rota | Descrição |
|---|---|---|
| GET | `/organizations/{id}/invitations/` | Lista convites da organização |
| POST | `/organizations/{id}/invitations/` | Cria e agenda envio do convite |
| POST | `/organizations/{id}/invitations/{invitation_id}/resend/` | Revoga token anterior e reenvia |
| POST | `/organizations/{id}/invitations/{invitation_id}/revoke/` | Revoga convite |
| POST | `/organizations/invitations/accept/` | Aceita token para o e-mail autenticado |

Tokens são retornados apenas no fluxo de entrega necessário e persistidos somente como hash. Convites expiram, são de uso único e não podem ser reutilizados.

## Configurações e perfil

| Método | Rota |
|---|---|
| GET/PATCH | `/organizations/{id}/settings/` |
| GET/PATCH | `/organizations/{id}/professional-profile/` |

O perfil profissional pertence à membership, permitindo dados diferentes em cada organização.

## Onboarding

| Método | Rota | Descrição |
|---|---|---|
| GET | `/organizations/{id}/onboarding/` | Retorna estado persistido |
| PATCH | `/organizations/{id}/onboarding/` | Salva etapa e seções permitidas |
| POST | `/organizations/{id}/onboarding/complete/` | Valida e conclui onboarding |

## Erros semânticos

- `ORGANIZATION_CONTEXT_REQUIRED`
- `ORGANIZATION_ACCESS_DENIED`
- `ORGANIZATION_SUSPENDED`
- `MEMBERSHIP_NOT_ACTIVE`
- `LAST_OWNER_REMOVAL`
- `INVITATION_EXPIRED`
- `INVITATION_ALREADY_USED`
- `INVITATION_INVALID`
- `ONBOARDING_INCOMPLETE`
- `CROSS_TENANT_RELATIONSHIP`

Respostas não devem revelar se uma organização ou recurso de outro tenant existe.
