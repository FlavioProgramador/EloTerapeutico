# Matriz de permissões por organização

A autorização utiliza capacidades da membership ativa. O papel global legado do usuário não concede acesso tenant-owned.

| Capacidade | Owner | Admin | Therapist | Receptionist | Finance | Viewer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Visualizar organização | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Alterar organização | ✓ | ✓ |  |  |  |  |
| Gerenciar membros | ✓ | ✓ |  |  |  |  |
| Gerenciar convites | ✓ | ✓ |  |  |  |  |
| Transferir propriedade | ✓ |  |  |  |  |  |
| Gerenciar billing | ✓ |  |  |  |  |  |
| Visualizar pacientes | ✓ | ✓ | vinculados | administrativo | administrativo | leitura mínima |
| Criar/alterar pacientes | ✓ | ✓ | vinculados | administrativo |  |  |
| Visualizar agenda | ✓ | ✓ | própria | ✓ | leitura | leitura |
| Gerenciar agenda | ✓ | ✓ | própria | ✓ |  |  |
| Visualizar prontuário | regras clínicas | regras clínicas | vinculados |  |  |  |
| Criar evolução | regras clínicas | regras clínicas | vinculados |  |  |  |
| Exportar prontuário | autorizado | autorizado | autorizado |  |  |  |
| Visualizar financeiro | ✓ | ✓ | limitado |  | ✓ | leitura |
| Gerenciar financeiro | ✓ | ✓ |  |  | ✓ |  |
| Gerenciar comunicações | ✓ | ✓ | vinculadas | operacional |  |  |
| Exportar relatórios | ✓ | ✓ | permitidos |  | financeiros |  |

## Regras invariantes

- Nenhum papel remove o último owner ativo.
- Admin não transfere propriedade.
- Therapist não recebe acesso automático a registros confidenciais de outro autor.
- Receptionist não acessa evolução, anamnese, plano terapêutico ou documento clínico interno.
- Finance não acessa conteúdo clínico.
- Viewer não executa escrita ou exportação sensível.
- Membership suspensa ou revogada não concede capacidade.
- Organização suspensa ou arquivada não aceita escrita operacional.

## Capacidades canônicas

```text
organization.view
organization.update
organization.manage_members
organization.manage_invitations
organization.manage_settings
organization.manage_billing
organization.transfer_ownership
patients.view
patients.create
patients.update
patients.archive
scheduling.view
scheduling.manage
records.view
records.create
records.update
records.export
records.view_confidential
finances.view
finances.manage
documents.view
documents.manage
forms.view
forms.manage
communications.view
communications.manage
reports.view
reports.export
```

Novas capacidades devem ser adicionadas à matriz centralizada e cobertas por testes. Não espalhar comparações diretas de papel em views ou serializers.
