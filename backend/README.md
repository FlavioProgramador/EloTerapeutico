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
│   ├── finances/
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

O domínio financeiro usa exclusivamente `apps.finances`; o app label histórico permanece `financeiro`.

As regras transacionais ficam em `services/`; consultas reutilizáveis e sensíveis ao proprietário ficam em `selectors`, managers ou querysets; a adaptação HTTP fica em views, serializers, filters e permissions.

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
- `/api/v1/finances/`;
- `/api/v1/documents/`;
- `/api/v1/reports/`;
- `/api/v1/forms/`;
- `/api/v1/billing/`;
- `/api/v1/communications/`;
- `/api/v1/public/communications/`.

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

## Regras de segurança

- nunca registre conteúdo clínico integral em logs ou auditoria;
- resolva pacientes, consultas, documentos e cobranças no escopo do usuário autenticado;
- valide relações recebidas no payload contra o mesmo proprietário;
- use transações e bloqueio de linha em mudanças de estado concorrentes;
- não versione arquivos `.env`, bancos locais, mídias privadas ou credenciais.
