# Comandos de qualidade

## Backend

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
pytest --create-db
ruff check .
ruff format --check .
mypy .
bandit -r apps infrastructure config -c pyproject.toml
pip-audit -r requirements.txt
```

## Frontend

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

## Docker

```bash
docker compose exec backend python manage.py check
docker compose exec backend pytest --create-db
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
```

## Medição

Registre no PR:

```text
Commit medido: <SHA>
Data: <AAAA-MM-DD>
Comando: <comando exato>
Resultado: <aprovado/falhou + resumo>
```

[Voltar](README.md)
