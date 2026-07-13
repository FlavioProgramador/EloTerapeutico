PYTHON ?= python

.PHONY: check migrations-check test coverage lint format format-check typecheck validate

check:
	$(PYTHON) manage.py check

migrations-check:
	$(PYTHON) manage.py makemigrations --check --dry-run

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=apps --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check . --fix

format-check:
	$(PYTHON) -m ruff format --check .

typecheck:
	$(PYTHON) -m mypy apps config

validate: check migrations-check lint format-check test
