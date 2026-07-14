#!/bin/bash
# startup.sh – Script de inicialização para Azure App Service (produção)
set -e

echo "==> Aplicando migrações..."
python manage.py migrate --noinput --settings=config.settings.production

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=config.settings.production

echo "==> Iniciando servidor Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
