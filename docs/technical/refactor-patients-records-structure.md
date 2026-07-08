# Refatoração de estrutura: patients e records

Esta branch aprofunda a organização dos apps `patients` e `records` após a refatoração inicial de pacotes do backend.

## Patients

### Admin

O arquivo `backend/apps/patients/admin.py` foi reduzido para manter apenas o registro principal do `PatientAdmin` e sua configuração central.

As responsabilidades auxiliares foram movidas para:

- `backend/apps/patients/admin_parts/filters.py`
- `backend/apps/patients/admin_parts/inlines.py`
- `backend/apps/patients/admin_parts/mixins.py`

### Models

O modelo `Patient` continua em `model_parts/patient.py`, mas escolhas e caminhos de upload foram separados:

- `backend/apps/patients/model_parts/choices.py`
- `backend/apps/patients/model_parts/paths.py`

Os aliases públicos `Patient.Status`, `Patient.Gender`, `Patient.PayerType`, etc. foram preservados.

## Records

### Admin

O arquivo `backend/apps/records/admin.py` foi reduzido para ponto de carregamento do Django Admin.

As classes administrativas foram separadas em:

- `backend/apps/records/admin_parts/anamnesis.py`
- `backend/apps/records/admin_parts/evolution.py`
- `backend/apps/records/admin_parts/addendum.py`
- `backend/apps/records/admin_parts/inlines.py`

### Models

O antigo `backend/apps/records/models/treatment.py` foi reduzido para fachada de compatibilidade.

A implementação foi separada em:

- `backend/apps/records/models/goals.py`
- `backend/apps/records/models/documents.py`
- `backend/apps/records/models/forms.py`
- `backend/apps/records/models/exports.py`
- `backend/apps/records/models/paths.py`

Os imports públicos antigos continuam funcionando via fachada.

## Validação recomendada

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```
