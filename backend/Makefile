PYTHON ?= python

.PHONY: install install-prod check migrations-check test coverage lint format format-check typecheck validate clean

install:
	$(PYTHON) -m pip install -r requirements.txt

install-prod:
	$(PYTHON) -m pip install -r requirements-prod.txt

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

validate: check migrations-check lint format-check typecheck test

clean:
	$(PYTHON) config/scripts/clean_backend.py
