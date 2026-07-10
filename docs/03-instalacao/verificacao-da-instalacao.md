# Verificação da instalação

## Backend

```bash
cd backend
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
```

Confirme:

```bash
curl http://localhost:8000/api/health/
```

Resultado esperado: `status` igual a `ok` quando o banco responde, ou `degraded` quando há falha de conexão.

## Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Acesse `http://localhost:3000`, crie uma conta fictícia de desenvolvimento e valide login/logout.

## Worker

Crie uma exportação em ambiente de teste e verifique logs do processo. Um job deve avançar de `PENDING` para `PROCESSING` e `COMPLETED` ou registrar falha controlada.

## Docker

```bash
docker compose ps
```

Backend e banco devem ficar saudáveis. O compose não define health check do frontend ou worker; valide seus logs e endpoints manualmente.

[Voltar](README.md)
