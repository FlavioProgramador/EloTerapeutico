# Backend do Elo Terapêutico

API REST em Django e Django REST Framework responsável pelos módulos clínicos, administrativos e de assinatura do Elo Terapêutico.

> O backend manipula dados pessoais, clínicos e financeiros. Antes de usar dados reais, configure segredos independentes, HTTPS, PostgreSQL gerenciado, armazenamento privado, backup, monitoramento e os provedores externos necessários.

## Tecnologias

- Python 3.12 recomendado;
- Django `>=5.0,<5.2`;
- Django REST Framework `>=3.15,<3.16`;
- PostgreSQL 15 em Docker e produção;
- SQLite para desenvolvimento local e testes quando apropriado;
- Simple JWT, django-filter e drf-spectacular;
- WeasyPrint para PDFs;
- Azure Blob Storage opcional;
- Argon2 para hash de senhas;
- cryptography/Fernet para campos textuais sensíveis;
- Django Unfold no backoffice.

## Estrutura

```text
backend/
├── apps/
│   ├── core/
│   ├── users/
│   ├── patients/
│   ├── records/
│   ├── scheduling/
│   ├── financeiro/
│   ├── documents/
│   ├── reports/
│   ├── forms/
│   ├── billing/
│   ├── communications/
│   └── audit/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── .env.example
```

O domínio de calendário usa exclusivamente o pacote Python `apps.scheduling`. O app label histórico do Django permanece como `agenda` para preservar tabelas, migrations, permissões, ContentTypes e relações persistidas.

As regras transacionais ficam em `services/`; consultas reutilizáveis e sensíveis ao proprietário ficam em `selectors/`, managers ou querysets; a adaptação HTTP fica em views, serializers, filters e permissions.

## Configuração sem Docker

```bash
cd backend
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## Execução com Docker

Na raiz do repositório:

```bash
cp .env.example .env
# configure POSTGRES_PASSWORD, SECRET_KEY, JWT_SECRET e FIELD_ENCRYPTION_KEY
docker compose up --build
```

Serviços principais:

- `backend`: API na porta `8000`;
- `db`: PostgreSQL 15 exposto apenas em `127.0.0.1:5432`;
- `worker`: processa exportações clínicas persistidas;
- `communications-worker`: processa a fila persistente de comunicações;
- `communications-scheduler`: agenda automações, retentativas e limpeza de tokens.

## API e documentação interativa

- API versionada: `http://localhost:8000/api/v1/`;
- health check: `http://localhost:8000/api/health/`;
- schema OpenAPI: `http://localhost:8000/api/schema/`;
- Swagger UI: `http://localhost:8000/api/docs/`;
- Redoc: `http://localhost:8000/api/redoc/`;
- Django Admin: `http://localhost:8000/admin/`.

Grupos principais da API:

- `/api/v1/auth/`;
- `/api/v1/patients/`;
- `/api/v1/records/`;
- `/api/v1/scheduling/`;
- `/api/v1/financeiro/`;
- `/api/v1/documents/`;
- `/api/v1/reports/`;
- `/api/v1/forms/`;
- `/api/v1/billing/`;
- `/api/v1/communications/`;
- `/api/v1/public/communications/`.

A antiga rota `/api/v1/agenda/` não é registrada. Consumidores devem usar `/api/v1/scheduling/`.

## Workers sem Docker

Em terminais separados:

```bash
cd backend
python manage.py run_export_worker
python manage.py process_communications --sleep 5
python manage.py schedule_communication_automations
python manage.py retry_failed_communications
python manage.py cleanup_expired_communication_tokens
```

## Testes e qualidade

```bash
cd backend
pytest --create-db
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
mypy .
python manage.py spectacular --file schema.yml --validate
```

O último comando depende do comando de management fornecido pelo drf-spectacular instalado no ambiente.

## Regras de segurança

- nunca registre conteúdo clínico integral em logs ou auditoria;
- resolva pacientes, consultas, documentos e cobranças no escopo do usuário autenticado;
- valide relações recebidas no payload contra o mesmo proprietário;
- use transações e bloqueio de linha em mudanças de estado concorrentes;
- valide assinatura ou token de webhooks antes de processar eventos;
- não reutilize segredos entre Django, JWT, criptografia de campos e webhooks;
- não versione arquivos `.env`, bancos locais, mídias privadas ou credenciais.

## Documentação detalhada

Consulte [`../docs/backend/README.md`](../docs/backend/README.md) para arquitetura, apps, API, autenticação, permissões, isolamento de dados, prontuário, billing, integrações, tarefas assíncronas, variáveis de ambiente, testes e troubleshooting.
