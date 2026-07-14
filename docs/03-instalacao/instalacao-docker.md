# Instalação com Docker

## Preparação

Na raiz:

```bash
cp .env.example .env
```

Preencha, no mínimo:

```text
SECRET_KEY=configure-um-segredo-local
JWT_SECRET=configure-outro-segredo-local
FIELD_ENCRYPTION_KEY=configure-uma-chave-local
POSTGRES_USER=postgres
POSTGRES_PASSWORD=configure-uma-senha-local
POSTGRES_DB=config
DATABASE_URL=postgres://postgres:configure-uma-senha-local@db:5432/config
```

Os exemplos são placeholders. Não os use em produção.

## Subir serviços

```bash
docker compose up --build
```

Em segundo plano:

```bash
docker compose up --build -d
```

## Operações úteis

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f worker
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py check
docker compose exec backend pytest --create-db
```

## Parar

```bash
docker compose down
```

Remover também volumes destrói o banco local:

```bash
docker compose down -v
```

Use a última opção somente quando a perda dos dados locais for intencional.

## Observações

- o backend executa migrations ao iniciar no compose de desenvolvimento;
- o frontend usa hot reload com volume montado;
- o worker precisa permanecer ativo para exportações;
- PostgreSQL é publicado apenas em loopback;
- o compose não representa uma arquitetura de produção.

[Voltar](README.md)
