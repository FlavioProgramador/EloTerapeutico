# Comandos úteis

Execute os comandos no diretório indicado e confirme o ambiente antes de operações destrutivas.

## Backend Django

A partir de `backend/`:

```bash
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate
python manage.py createsuperuser
python manage.py spectacular --file schema.yml --validate
python manage.py runserver
```

`run_export_worker` é um comando legado de compatibilidade e não representa o worker atual do Docker Compose. Prefira Celery na fila `exports`.

## Celery sem Docker

A partir de `backend/`, em terminais separados:

```bash
celery -A config worker --loglevel=INFO --queues=default --concurrency=1
celery -A config worker --loglevel=INFO --queues=exports --concurrency=1
celery -A config worker --loglevel=INFO --queues=uploads --concurrency=1
celery -A config worker --loglevel=INFO --queues=communications --concurrency=2
celery -A config beat --loglevel=INFO
```

Sem coordenação adicional, mantenha apenas uma instância de Celery Beat por ambiente.

## Testes e qualidade do backend

A partir de `backend/`:

```bash
python apps/core/quality/check_backend_architecture.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file schema.yml --validate
ruff check .
mypy .
pytest --create-db
```

Ferramentas de segurança usadas por workflows específicos devem ser executadas conforme a configuração existente no repositório, por exemplo `pip-audit` e Bandit quando instalados pelo respectivo job.

## Frontend

A partir de `frontend/`:

```bash
npm ci
npm run lint
npm run typecheck
npm test
npm run test:coverage
npm run test:auth
npm run build
```

## Documentação

A partir da raiz:

```bash
python scripts/validate_docs.py
docker compose config
docker compose config --services
```

A saída expandida do Compose pode conter valores locais. Não a publique quando houver segredos.

## Docker Compose

Subir e inspecionar:

```bash
docker compose up --build
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose logs -f redis
```

Workers e scheduler:

```bash
docker compose logs -f celery-worker-default
docker compose logs -f celery-worker-exports
docker compose logs -f celery-worker-uploads
docker compose logs -f celery-worker-communications
docker compose logs -f celery-beat
```

Checks no backend:

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend pytest --create-db
```

Reiniciar componentes:

```bash
docker compose restart backend
docker compose restart frontend
docker compose restart celery-worker-default
docker compose restart celery-worker-exports
docker compose restart celery-worker-uploads
docker compose restart celery-worker-communications
docker compose restart celery-beat
```

Parar preservando volumes:

```bash
docker compose down
```

Remover containers e volumes:

```bash
docker compose down -v
```

> **Destrutivo:** `down -v` remove o banco PostgreSQL local e os demais volumes nomeados.

## Git

```bash
git status -sb
git diff --check
git diff --stat
git log --oneline --decorate -10
```

[Voltar](README.md)
