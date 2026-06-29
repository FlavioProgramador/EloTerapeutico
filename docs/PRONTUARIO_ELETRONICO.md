# Prontuário Eletrônico

O módulo de prontuário reúne a navegação entre pacientes, evoluções clínicas, anamnese, plano terapêutico e documentos em um espaço de trabalho integrado.

## Estrutura do frontend

Os componentes ficam em `frontend/src/features/records`:

- `components/record-workspace.tsx`: coordena consultas, abas, ações e estados da tela;
- `components/patient-selector.tsx`: busca e troca de paciente, com drawer em telas menores;
- `components/record-header.tsx`: identificação do paciente e ações principais;
- `components/record-overview.tsx`: indicadores e painel compacto de apoio;
- `components/evolution-timeline.tsx`: histórico cronológico e detalhe selecionado;
- `components/evolution-editor.tsx`: formulário estruturado com recuperação local de rascunho;
- `components/anamnesis-tab.tsx`: anamnese em seções recolhíveis;
- `components/goals-tab.tsx`: acompanhamento do plano terapêutico;
- `components/documents-tab.tsx`: envio, download e arquivamento de documentos;
- `services/record-workspace.service.ts`: chamadas da API;
- `hooks/use-record-workspace.ts`: cache e mutações com TanStack Query;
- `types.ts`: contratos TypeScript do módulo.

## Estrutura do backend

O app `backend/apps/records` preserva os modelos e endpoints anteriores e acrescenta:

- `extended_models.py`: perfil ampliado da anamnese, dados estruturados da evolução e versões imutáveis;
- `treatment_models.py`: metas terapêuticas e documentos clínicos;
- `clinical_serializers.py`: validações e integração dos novos modelos;
- `clinical_views.py`: endpoints do espaço clínico;
- migrations `0003`, `0004` e `0005`;
- testes em `backend/apps/records/tests`.

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
- metas podem ser pausadas, concluídas, reabertas ou arquivadas;
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
