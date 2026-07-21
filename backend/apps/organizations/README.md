# Domínio de organizações

O app `organizations` define o tenant explícito do Elo Terapêutico. Uma organização pode representar:

- um profissional que trabalha sozinho (`individual`);
- uma clínica com equipe (`clinic`);
- uma empresa ou unidade administrativa (`company`).

O modelo é o mesmo nos três casos. Um profissional individual começa com uma organização e uma membership `owner`; quando convida outras pessoas, os dados existentes permanecem no mesmo tenant.

## Entidades

- `Organization`: espaço isolado de trabalho.
- `OrganizationMembership`: vínculo entre usuário, organização e papel.
- `OrganizationInvitation`: convite com token persistido somente como hash.
- `ProfessionalProfile`: perfil profissional específico da membership.
- `OrganizationSettings`: preferências institucionais e de atendimento.

## Contexto ativo

O frontend envia `X-Organization-ID` ao BFF do Next.js. O BFF valida o formato UUID e encaminha o header à API Django. O backend nunca confia apenas no valor recebido: ele exige uma membership ativa do usuário para a organização informada.

Sem header:

1. a membership marcada como padrão é utilizada;
2. com apenas uma membership ativa, ela é selecionada;
3. com várias memberships e nenhuma padrão, a API exige seleção explícita;
4. sem membership ativa, o acesso tenant-owned é recusado.

## Arquitetura

```text
URL -> View -> Serializer/Permission -> Service/Selector -> Model
```

Views não acessam ORM diretamente. Services recebem `organization` explicitamente e selectors sempre filtram recursos tenant-owned.

## Novos models tenant-owned

Ao adicionar uma entidade pertencente à clínica:

1. adicione `organization = ForeignKey(Organization, on_delete=PROTECT)`;
2. inclua índices com `organization` para os filtros principais;
3. valide relações cruzadas em `clean()` e no service transacional;
4. derive o tenant do contexto autenticado, nunca do payload comum;
5. adicione backfill expand -> backfill -> validate -> contract;
6. inclua o model em `audit_tenant_integrity`;
7. teste acesso entre duas organizações diferentes.

## Comandos

```bash
python manage.py backfill_organizations --dry-run
python manage.py backfill_organizations --batch-size 500 --report-file reports/backfill.json
python manage.py audit_tenant_integrity --format=json --report-file reports/tenant-audit.json
python manage.py audit_tenant_integrity --fail-on-error
python manage.py repair_tenant_integrity --dry-run
```

O comando de reparo é conservador: somente associa relações determinísticas. Dados ambíguos permanecem para revisão manual.

## Billing

O catálogo de planos continua global. Durante esta fase, a assinatura permanece vinculada ao proprietário da organização por uma camada de adaptação. O backfill não cria assinaturas para membros nem duplica cobranças.
