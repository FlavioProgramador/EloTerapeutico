# Prontuário Eletrônico

O módulo de prontuário reúne a navegação entre pacientes, evoluções clínicas, anamnese, plano terapêutico e documentos em um espaço de trabalho integrado.

## Estrutura do frontend

Os componentes ficam em `frontend/src/features/records`:

- `components/record-workspace.tsx`: coordena consultas, abas, ações e estados da tela;
- `components/record-tabs-nav.tsx`: navegação compartilhada das abas, sincronizada com o parâmetro `tab` da URL;
- `components/patient-selector.tsx`: busca e troca de paciente, com drawer em telas menores;
- `components/record-header.tsx`: identificação do paciente e ações principais;
- `components/record-overview.tsx`: indicadores e painel compacto de apoio;
- `components/evolution-timeline.tsx`: busca, filtros, linha do tempo e detalhe selecionado;
- `components/evolution-editor.tsx`: formulário estruturado com recuperação local de rascunho;
- `components/anamnesis-tab.tsx`: anamnese por seções, modo leitura/edição e resumo de preenchimento;
- `components/goals-tab.tsx`: objetivo principal, metas, progresso geral e estratégias terapêuticas;
- `components/documents-tab.tsx`: busca, filtros, tabela, painel de detalhes e upload seguro;
- `services/record-workspace.service.ts`: chamadas da API;
- `hooks/use-record-workspace.ts`: cache, carregamento independente e mutações com TanStack Query;
- `types.ts`: contratos TypeScript do módulo.

## Navegação das abas

As abas disponíveis são:

- `evolutions`: Histórico de evoluções;
- `appointments`: Consultas realizadas e agendadas;
- `documents`: Arquivos e anexos;
- `forms`: Formulários clínicos;
- `exports`: Exportações em PDF geradas.

A aba ativa é persistida na URL, por exemplo:

```text
/dashboard/records/42?tab=appointments
```

A troca utiliza navegação do App Router sem recarregar toda a página e preserva o paciente selecionado. Cada consulta clínica é habilitada somente quando sua respectiva aba está ativa.

## Histórico de evoluções

A aba oferece:

- busca no conteúdo clínico e no profissional responsável;
- filtros por período, modalidade e status;
- ordenação cronológica;
- paginação visual da lista carregada;
- seleção com destaque;
- resumo de data, horário, duração, modalidade e status;
- detalhe estruturado por queixa, relato, estado emocional, observações, intervenções, evolução percebida, orientações, encaminhamentos e próximos passos;
- indicadores de documentos, metas e versões vinculadas;
- ações de edição, duplicação, impressão e exportação.

Evoluções finalizadas continuam bloqueadas para edição direta. Alterações autorizadas preservam snapshots auditáveis.

## Consultas (Appointments)

A aba de Consultas permite:
- Visualizar a lista cronológica de consultas (com paginação e busca);
- Associar ou criar novas evoluções diretamente a partir de um atendimento realizado;
- Exibir os status da evolução associada (como "Pendente" ou "Finalizada").

## Formulários Clínicos (Forms)

Esta aba exibe os questionários psicométricos (como o BAI - Inventário de Ansiedade Beck, e BDI - Inventário de Depressão Beck) preenchidos ou pendentes. Ela permite:
- Visualizar as respostas estruturadas de questionários passados;
- Responder a novos formulários através de modais interativos integrados com salvamento no backend.

## Exportações e Relatórios (Exports)

As exportações de prontuário em PDF utilizam processamento assíncrono em fila persistida e isolamento de locks. A aba permite:
- Visualizar a listagem de exportações solicitadas, tamanhos dos arquivos e statuses;
- Iniciar uma nova exportação em segundo plano;
- Fazer download seguro e autenticado dos PDFs concluídos;
- Polling controlado pelo frontend que consome recursos de rede apenas quando existem jobs ativamente em processamento.

## Documentos

A aba oferece:

- busca por nome e descrição;
- filtro por categoria;
- tabela responsiva;
- paginação no cliente sobre a coleção retornada pela API;
- painel lateral de detalhes;
- download autenticado;
- edição de categoria e descrição;
- arquivamento lógico;
- seleção por clique ou arrastar e soltar;
- envio de múltiplos arquivos de forma sequencial;
- validação de extensão e tamanho antes do envio;
- validação adicional de MIME type e tamanho no backend.

O backend também retorna status, profissional responsável, versão e evolução vinculada. Os arquivos não possuem URL pública permanente.

A geração por modelos e o fluxo de assinatura continuam desabilitados até existir implementação de backend, revisão clínica e regras de consentimento adequadas.

## Estrutura do backend

O app `backend/apps/records` utiliza:

- `models.py`: modelo `Evolution` com campo `is_confidential` e permissões customizadas;
- `treatment_models.py`: novos modelos `ClinicalFormResponse` e `ClinicalExport` (com dados de rastreamento do worker e FileField privado);
- `clinical_serializers.py`: serializers das novas entidades e otimização do serializer de agendamentos;
- `clinical_views.py`: endpoints para formulários e exportações assíncronas com isolamento e controle de privacidade;
- `utils.py`: utilitários de renderização segura de Markdown (XSS-safe) e fetcher de WeasyPrint seguro (SSRF-safe);
- `management/commands/run_export_worker.py`: worker persistente com tratamento de jobs presos e locks eficientes;
- migrations até `0008_alter_evolution_options`;
- testes robustos em `backend/apps/records/tests/test_clinical_refactor.py`.

A refatoração visual das abas não adicionou migrations.

## Metadados expostos pela API

Foram acrescentados aos contratos existentes:

- anamnese: `status`, `status_display` e `updated_by_name`;
- evolução: `attached_documents_count` e `linked_goal_ids`;
- meta: `created_by_name`;
- documento: `status`, `status_display`, `uploaded_by_name` e `evolution_date`.

## Endpoints principais

Todos os endpoints exigem autenticação.

```text
GET    /api/v1/records/patients/{patient_id}/workspace/
GET    /api/v1/records/patients/{patient_id}/clinical-anamnesis/
PATCH  /api/v1/records/patients/{patient_id}/clinical-anamnesis/
GET    /api/v1/records/patients/{patient_id}/anamnesis-versions/
GET    /api/v1/records/patients/{patient_id}/clinical-evolutions/
POST   /api/v1/records/patients/{patient_id}/clinical-evolutions/
GET    /api/v1/records/clinical-evolutions/{id}/
PATCH  /api/v1/records/clinical-evolutions/{id}/
POST   /api/v1/records/clinical-evolutions/{id}/finalize/
POST   /api/v1/records/clinical-evolutions/{id}/duplicate/
GET    /api/v1/records/patients/{patient_id}/goals/
POST   /api/v1/records/patients/{patient_id}/goals/
PATCH  /api/v1/records/goals/{id}/
DELETE /api/v1/records/goals/{id}/
GET    /api/v1/records/patients/{patient_id}/documents/
POST   /api/v1/records/patients/{patient_id}/documents/
PATCH  /api/v1/records/documents/{id}/
DELETE /api/v1/records/documents/{id}/
GET    /api/v1/records/documents/{id}/download/
GET    /api/v1/records/patients/{patient_id}/export-pdf/
GET    /api/v1/records/patients/{patient_id}/ai-summary/
```

## Regras clínicas

- evoluções novas começam como rascunho;
- a finalização bloqueia a edição direta;
- alterações autorizadas preservam uma versão anterior;
- a anamnese pode ser salva por seção e mantém histórico de versões;
- metas podem ser pausadas, concluídas, reabertas, reordenadas ou arquivadas;
- documentos são arquivados por exclusão lógica;
- o resumo por IA permanece indisponível enquanto não houver provedor seguro, consentimento e configuração explícita.

## Segurança

- o backend valida o vínculo entre paciente e terapeuta em cada endpoint;
- administradores mantêm o acesso previsto na arquitetura atual;
- IDs recebidos pelo frontend nunca substituem a autorização do backend;
- campos clínicos complementares usam o mecanismo de criptografia existente;
- arquivos são baixados somente por rota autenticada;
- o nome físico do arquivo não contém o nome do paciente;
- uploads possuem limite de 10 MB e lista de tipos permitidos;
- leitura, criação, alteração, exportação e arquivamento geram eventos de auditoria;
- testes e exemplos usam exclusivamente dados fictícios.

> O projeto ainda não possui um modelo definitivo de clínica ou organização. Portanto, o isolamento implementado neste módulo segue o vínculo atual entre paciente e terapeuta. O isolamento multi-tenant completo deve ser aplicado quando a entidade de clínica for incorporada ao domínio.

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
