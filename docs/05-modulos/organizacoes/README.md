# Organizações e multi-tenancy

## Identificação

| Campo | Descrição |
| --- | --- |
| Backend | `backend/apps/organizations/` |
| Frontend | `frontend/src/features/organizations/`, `frontend/src/contexts/organization.tsx` e páginas de configuração |
| API | `/api/v1/organizations/` e `/api/v1/organization-invitations/accept/` |
| Situação | 🟡 implementado parcialmente |
| Maturidade | Domínio explícito presente; ownership legado ainda requer revisão transversal |

O módulo define o contexto institucional em que usuários, pacientes, agenda, prontuário, financeiro e demais recursos são acessados. Uma organização pode representar um profissional individual, uma clínica ou uma empresa.

## Conceitos

### Usuário

Conta autenticável. Um usuário pode participar de mais de uma organização.

### Terapeuta

Papel profissional exercido por um usuário. O terapeuta não é o tenant; ele participa de uma organização por meio de uma membership.

### Organização

Tenant lógico com nome, slug, tipo, documento, contato, timezone, status, onboarding e usuário criador.

Tipos:

- `individual` — profissional individual;
- `clinic` — clínica;
- `company` — empresa.

Estados:

- `active`;
- `suspended`;
- `archived`.

### Membership

Vínculo entre usuário e organização. Armazena papel, status, organização padrão, data de entrada e usuário que realizou o convite.

Papéis:

- `owner`;
- `admin`;
- `therapist`;
- `receptionist`;
- `finance`;
- `viewer`.

Estados:

- `invited`;
- `active`;
- `suspended`;
- `revoked`.

Constraints impedem membership duplicada do mesmo usuário na organização e mais de uma organização padrão por usuário.

### Proprietário

Membership com papel `owner`. O proprietário não deve ser confundido com campos legados de ownership que ainda apontam diretamente para terapeuta ou usuário.

### Perfil profissional

`ProfessionalProfile` pertence à membership e contém nome de exibição, título, conselho, especialidades, biografia, contato público, duração e valor padrão de sessão e modalidades aceitas.

### Configurações da organização

`OrganizationSettings` armazena timezone, moeda, duração padrão, regras de agendamento, telemedicina, lembretes e identidade usada em documentos.

### Assinatura SaaS

Billing controla plano, pagamento e entitlements. A assinatura não substitui organização, membership ou autorização. Ela define acesso comercial ao produto, enquanto o tenant define o escopo dos dados.

## Entidades

| Entidade | Responsabilidade |
| --- | --- |
| `Organization` | Tenant, identidade institucional, status e onboarding |
| `OrganizationMembership` | Relação usuário-organização, papel e estado |
| `OrganizationInvitation` | Convite temporário por e-mail, token por hash e expiração |
| `OrganizationSettings` | Regras operacionais e identidade institucional |
| `ProfessionalProfile` | Dados profissionais associados a uma membership |

## Convites

Convites armazenam e-mail, papel, organização, autor, hash do token, expiração e estado. O token bruto não deve ser persistido nem registrado em logs.

Estados:

- `pending`;
- `accepted`;
- `revoked`;
- `expired`.

Uma constraint impede mais de um convite pendente para o mesmo e-mail na mesma organização.

## Onboarding

A organização mantém `onboarding_status`, `onboarding_step` e `onboarding_completed_at`.

Estados:

- `pending`;
- `in_progress`;
- `completed`.

O frontend possui páginas para onboarding, organização, equipe, atendimento e perfil profissional. Concluir onboarding não substitui validação de assinatura, permissões ou configuração de integrações.

## Contexto ativo no frontend

`OrganizationProvider` carrega `/api/v1/organizations/context/`, mantém a organização e membership ativas e oferece troca de organização.

Ao trocar de organização, o frontend:

1. chama `POST /api/v1/organizations/{id}/activate/`;
2. persiste o ID selecionado no storage da feature;
3. atualiza o contexto autorizado retornado pelo backend;
4. remove queries de domínio do TanStack Query;
5. recarrega o contexto.

A invalidação das queries reduz o risco de reutilizar cache pertencente à organização anterior. O valor guardado no navegador é preferência de contexto, não autorização.

## Header de organização

Quando aplicável, o BFF encaminha:

```text
X-Organization-ID: <uuid-da-organizacao>
```

Em produção, `config.settings.production`:

- registra `apps.organizations.apps.OrganizationsConfig`;
- usa `TenantSubscriptionJWTAuthentication`;
- permite `x-organization-id` no CORS;
- define `TENANT_ENFORCEMENT_ENABLED=True`.

A ausência, falsificação ou seleção de organização sem membership ativa deve falhar de forma segura.

## Desenvolvimento e produção

| Item | Desenvolvimento | Produção |
| --- | --- | --- |
| App de organizações | Pode coexistir com compatibilidade legada | Obrigatório |
| Autenticação | Pode manter transição de ownership | Tenant-aware |
| Enforcement | Pode estar desativado durante migração | Obrigatório |
| Header | Usado conforme fluxo | Validado em todas as requisições tenant-aware |
| Ownership legado | Pode existir em módulos migrando | Deve ser auditado antes de dados reais |

A diferença permite migração aditiva, mas não autoriza implantação sem revisar todos os domínios.

## API

Rotas principais:

```text
GET, POST /api/v1/organizations/
GET       /api/v1/organizations/context/
GET, PATCH /api/v1/organizations/{organization_id}/
POST      /api/v1/organizations/{organization_id}/activate/
GET, POST /api/v1/organizations/{organization_id}/members/
GET, PATCH, DELETE /api/v1/organizations/{organization_id}/members/{membership_id}/
GET, POST /api/v1/organizations/{organization_id}/invitations/
POST      /api/v1/organizations/{organization_id}/invitations/{invitation_id}/{action}/
GET, PATCH /api/v1/organizations/{organization_id}/settings/
GET, PATCH /api/v1/organizations/{organization_id}/professional-profile/
GET, PATCH /api/v1/organizations/{organization_id}/onboarding/
POST      /api/v1/organizations/{organization_id}/onboarding/complete/
POST      /api/v1/organizations/invitations/accept/
POST      /api/v1/organization-invitations/accept/
```

Respostas públicas devem ser genéricas quando necessário para evitar enumeração de contas ou convites.

## Permissões

A autorização deve considerar:

- autenticação válida;
- membership ativa;
- organização ativa;
- papel necessário;
- ownership do objeto dentro da organização;
- entitlement da assinatura quando aplicável.

Ocultar opções no frontend não substitui permissions e filtros no backend.

## Isolamento de dados

Selectors e services devem aplicar tenant antes de carregar ou alterar dados. Relações recebidas no payload devem ser validadas contra a mesma organização.

Riscos que exigem revisão transversal:

- models legados com `owner`, `therapist` ou `created_by` sem `organization` explícita;
- selectors que filtram apenas pelo usuário;
- tasks Celery que recebem um ID sem reconstruir o contexto de tenant;
- exportações ou relatórios com relações cruzadas;
- caches sem organização na chave;
- webhooks que resolvem registros apenas por ID externo;
- páginas que reutilizam cache após troca de organização.

## Segurança

- IDs de organização não concedem acesso isoladamente;
- membership é verificada no servidor;
- convites usam token temporário persistido por hash;
- alteração de papel, suspensão e revogação devem ser auditadas;
- organização suspensa ou arquivada não deve permitir operação normal;
- logs devem usar IDs técnicos, sem conteúdo clínico;
- superusuário e Django Admin exigem política operacional própria.

## Testes esperados

- criação de organização individual e clínica;
- constraints de membership e organização padrão;
- papéis e permissões;
- convite, expiração, revogação e aceite;
- token persistido somente por hash;
- troca de organização;
- header ausente, inválido e não autorizado;
- organização suspensa ou arquivada;
- isolamento com dois usuários e duas organizações;
- invalidação de cache do frontend;
- tasks, relatórios, exportações e integrações no tenant correto.

## Limitações atuais

- o domínio explícito existe, mas a migração de ownership não é presumida como concluída em todos os apps;
- cobertura E2E de troca de organização deve ser ampliada;
- recursos públicos precisam resolver o tenant sem ambiguidade;
- permissões do Admin precisam ser revisadas para equipes reais;
- Billing continua associado à contratação da organização e não cria cobrança por membro;
- backup, restauração e staging devem provar isolamento antes de dados reais.

## Referências

- `backend/apps/organizations/`;
- `backend/config/settings/production.py`;
- `backend/config/urls.py`;
- `frontend/src/contexts/organization.tsx`;
- `frontend/src/features/organizations/`;
- `frontend/src/app/onboarding/`;
- `frontend/src/app/dashboard/configuracoes/organizacao/`;
- `frontend/src/app/dashboard/configuracoes/equipe/`;
- [ADR de multi-tenancy](../../16-decisoes-arquiteturais/ADR-multi-tenancy.md);
- [Matriz de módulos](../../17-referencia/matriz-de-modulos.md).

[Voltar ao índice de módulos](../README.md)
