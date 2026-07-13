# Execução

## Backend

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

## Worker

```bash
cd backend
python manage.py run_export_worker
```

## Frontend

```bash
cd frontend
npm run dev
```

## Produção local simulada

Backend:

```bash
cd backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Frontend:

```bash
cd frontend
npm run build
npm run start
```

Isso não substitui o settings de produção, HTTPS, proxy, storage privado, banco gerenciado, segredos e monitoramento.

## Dados iniciais

Migrations incluem seeds para planos de billing e biblioteca de documentos. Não execute scripts de seed desconhecidos em produção sem revisar idempotência e conteúdo.

[Voltar](README.md)
