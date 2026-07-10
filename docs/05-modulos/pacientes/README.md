# Módulo de pacientes

**Status: implementado.**

## Finalidade e atores

Gerenciar o cadastro administrativo do paciente e servir de raiz para agenda, prontuário, financeiro, documentos e formulários. Terapeutas e administradores gerenciam; secretárias têm acesso administrativo limitado.

## Entidades

### Patient

Campos principais:

- nome civil/social, foto, CPF, RG, nascimento, gênero, estado civil e profissão;
- e-mail, telefone, WhatsApp e endereço JSON;
- terapeuta responsável;
- status: `active`, `evaluation`, `waiting_return`, `discharged`, `inactive`, `archived`;
- tipo de atendimento, modalidade e pagador;
- convênio, valor de sessão, frequência e lembretes;
- contato de emergência;
- responsável legal e financeiro;
- consentimento administrativo, notas e tags;
- `deleted_at`, criação e atualização.

### PatientProfessional

Relaciona outros profissionais ao paciente conforme implementação em `model_parts/professional.py`.

### PatientRegistrationInvite

Suporta convite/formulário de cadastro com fluxo próprio.

## Regras de negócio

- CPF é opcional, mas único quando informado e passa por validação;
- o terapeuta é protegido contra exclusão enquanto possuir pacientes;
- listagens usam manager que exclui arquivados por padrão;
- desativação e restauração passam por serviços de lifecycle;
- exportação CSV mascara CPF e registra auditoria;
- importação CSV é exclusiva para terapeuta, aceita até 2 MB e 500 linhas, exige UTF-8 e colunas `full_name`, `cpf`, `birth_date`;
- importação faz preview antes da confirmação e ocorre em transação;
- dashboard clínico só inclui evolução/documentos para terapeuta ou administrador autorizado pelo fluxo;
- secretária pode criar paciente, mas não alterar conteúdo de objeto existente pela permission principal.

## API principal

| Método | Rota | Uso |
| --- | --- | --- |
| GET/POST | `/api/v1/patients/` | Listar/criar |
| GET/PATCH/PUT/DELETE | `/api/v1/patients/{id}/` | Detalhe e operações padrão autorizadas |
| POST | `/api/v1/patients/{id}/deactivate/` | Desativar |
| POST | `/api/v1/patients/{id}/restore/` | Restaurar |
| GET | `/api/v1/patients/{id}/form/` | Dados de edição |
| GET | `/api/v1/patients/{id}/dashboard/` | Workspace resumido |
| GET | `/api/v1/patients/dashboard-metrics/` | Métricas |
| POST | `/api/v1/patients/import-csv/` | Preview/importação |
| GET | `/api/v1/patients/export-csv/` | Exportação autorizada |
| GET/POST | `/api/v1/patients/{id}/reminders/` | Preferências/lembretes |

O ViewSet também compõe actions de formulário e convite. Consulte o schema OpenAPI da revisão executada para o contrato exato dessas actions.

## Frontend

`features/patients` contém serviço, hooks, listagem, formulário, ações e workspace. A rota de detalhe é `/dashboard/patients/[id]`. Estados de loading, erro, vazio e sucesso devem ser preservados.

## Permissões

- terapeuta: pacientes acessíveis conforme selector e gestão permitida;
- administrador: acesso conforme selector e permission;
- secretária: métodos de coleção `GET/POST`, leitura de objeto, sem edição clínica;
- isolamento real depende de `patients_accessible_to` e `can_manage_patient`.

## Segurança e auditoria

- validadores de CPF e telefone;
- exportação com CPF mascarado;
- importação limitada e transacional;
- logs usam representação técnica mínima;
- dados cadastrais e responsáveis são pessoais e devem ser minimizados;
- o modelo principal não criptografa todos os campos cadastrais individualmente; proteção depende também do banco, storage e acesso.

## Testes

Há suítes para CRUD, dashboard, listagem refatorada, lembretes, segurança e regressões.

## Limitações

- CPF único global pode conflitar com futura separação por tenant;
- consentimento é um boolean/timestamp, não um módulo jurídico completo;
- arquivamento não equivale a exclusão ou anonimização;
- importação não deve receber dados reais fora de ambiente autorizado.

[Voltar aos módulos](../README.md)
