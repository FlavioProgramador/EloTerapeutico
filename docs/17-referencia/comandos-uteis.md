# Comandos úteis

## Django

```bash
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py run_export_worker
```

## Testes e qualidade

```bash
pytest --create-db
ruff check .
mypy .
bandit -r apps core infrastructure elo_terapeutico -c pyproject.toml
pip-audit -r requirements/base.txt
npm run lint
npm run typecheck
npm test
npm run build
```

## Docker

```bash
docker compose up --build
docker compose ps
docker compose logs -f backend
docker compose logs -f worker
docker compose exec backend python manage.py check
docker compose down
```

## Git

```bash
git status
git diff --check
git diff --stat
git log --oneline --decorate -10
```

[Voltar](README.md)
