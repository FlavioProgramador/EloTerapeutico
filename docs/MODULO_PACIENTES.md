# Módulo de Pacientes

O módulo de Pacientes centraliza cadastro, busca, acompanhamento administrativo e acesso rápido ao prontuário. A interface foi organizada para manter a listagem e o paciente selecionado no mesmo contexto, evitando navegações desnecessárias.

## Estrutura do frontend

Os componentes principais ficam em `frontend/src/features/patients`:

- `components/patients-workspace.tsx`: coordena listagem, métricas, seleção e modais;
- `components/patient-toolbar.tsx`: cabeçalho, busca, status e filtros avançados;
- `components/patient-metrics.tsx`: indicadores calculados pelo backend;
- `components/patient-list-panel.tsx`: tabela responsiva, seleção e paginação;
- `components/patient-detail-panel.tsx`: resumo operacional do paciente selecionado;
- `components/new-patient-modal.tsx`: cadastro organizado por seções;
- `components/patient-import-modal.tsx`: pré-validação e importação de CSV;
- `hooks/use-patient-dashboard.ts`: consultas do painel e exportação;
- `hooks/use-patient-workspace.ts`: estado dos filtros, paginação e URL;
- `types.ts`: contratos específicos do painel.

A rota `frontend/src/app/dashboard/patients/page.tsx` apenas renderiza o espaço de trabalho dentro de `Suspense`.

## Estrutura do backend

O app `backend/apps/patients` acrescenta:

- dados administrativos e operacionais no model `Patient`;
- status `active`, `evaluation`, `waiting_return`, `discharged`, `inactive` e `archived`;
- etiquetas, modalidade, tipo de atendimento, convênio, frequência e contatos complementares;
- consultas anotadas em `dashboard_queries.py`, evitando N+1;
- métricas e painel lateral em `dashboard_actions.py`;
- serializer resumido com CPF mascarado;
- importação CSV com pré-visualização;
- exportação CSV limitada ao queryset autorizado;
- migrations de compatibilidade e sincronização de metadados.

## Endpoints

Todos exigem autenticação.

```text
GET    /api/v1/patients/
POST   /api/v1/patients/
GET    /api/v1/patients/{id}/
PATCH  /api/v1/patients/{id}/
DELETE /api/v1/patients/{id}/
POST   /api/v1/patients/{id}/deactivate/
POST   /api/v1/patients/{id}/restore/
GET    /api/v1/patients/{id}/dashboard/
GET    /api/v1/patients/dashboard-metrics/
GET    /api/v1/patients/export-csv/
POST   /api/v1/patients/import-csv/
```

## Busca e filtros

A listagem aceita:

```text
search
status
therapist
modality
payer_type
attendance_type
tag
no_next_session
birth_date_gte
birth_date_lte
created_at_gte
created_at_lte
page
page_size
ordering
```

A busca cobre nome, nome social, e-mail, telefone, WhatsApp e CPF normalizado.

## Importação CSV

O arquivo deve usar UTF-8, possuir até 2 MB e no máximo 500 linhas. As colunas obrigatórias são:

```text
full_name,cpf,birth_date
```

Também são aceitas:

```text
email,phone,gender,status,modality,payer_type,therapist
```

O fluxo ocorre em duas etapas:

1. `confirm=false`: valida estrutura, campos e duplicidades sem persistir dados;
2. `confirm=true`: cria os registros somente quando não existem erros ou duplicidades.

O frontend disponibiliza um modelo CSV para download.

## Exportação

A exportação respeita os mesmos filtros da tela e o queryset autorizado do usuário. O CPF é exportado mascarado. A ação é registrada na auditoria.

## Permissões e privacidade

- terapeutas acessam somente pacientes vinculados a eles;
- administradores acessam os pacientes autorizados pelo modelo atual;
- secretários mantêm as permissões administrativas previstas no projeto;
- identificadores enviados pelo frontend não substituem a autorização do backend;
- CPF completo não é retornado na listagem nem no painel lateral;
- a leitura do painel e as exportações geram eventos de auditoria;
- DELETE arquiva o cadastro; a ação `deactivate` encerra o acompanhamento sem classificá-lo como arquivado;
- nenhum conteúdo fictício é apresentado como resumo de IA quando o provedor não está configurado.

> O projeto ainda não possui uma entidade definitiva de clínica ou organização. O isolamento atual utiliza o vínculo entre paciente e terapeuta. O isolamento multi-tenant por clínica deve ser aplicado quando esse domínio for incorporado.

## Validação

Backend:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
pytest --cov=apps --cov=core
```

Frontend:

```bash
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
```
