# Testes backend

## Ferramentas

- pytest 9;
- pytest-django;
- pytest-cov;
- factory-boy e Faker;
- Ruff;
- mypy/django-stubs;
- Bandit;
- pip-audit.

`pyproject.toml` usa settings de teste, `--reuse-db`, markers estritos e traceback curto.

## Suítes encontradas

- usuários: autenticação, logout, reset e regressões;
- auditoria: minimização e IP;
- pacientes: CRUD, dashboard, listagem e segurança;
- records: workspace, documentos, uploads, exportações, confidencialidade, templates e views legadas;
- agenda: fluxos completos, telemedicina e performance;
- financeiro: transações, mensalidades, dashboard, cobertura e performance;
- billing: checkout, gateway, redaction e segurança.

## Comandos

```bash
cd backend
pytest --create-db
pytest apps/records/tests -q
pytest --cov=apps --cov=core --cov-report=term-missing
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
mypy .
```

## Limitações

- módulos com `ignore_errors` reduzem garantia do mypy;
- SQLite em testes não cobre toda semântica de locking do PostgreSQL;
- integrações reais devem permanecer mockadas em testes comuns e possuir ambiente sandbox separado;
- cobertura deve ser registrada com SHA/data.

[Voltar](README.md)
