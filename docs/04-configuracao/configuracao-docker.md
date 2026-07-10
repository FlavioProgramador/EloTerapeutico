# Configuração Docker

## Serviços locais

| Serviço | Imagem/build | Comando |
| --- | --- | --- |
| `db` | `postgres:15-alpine` | servidor PostgreSQL |
| `backend` | `backend/Dockerfile` | migrate + runserver |
| `frontend` | `frontend/Dockerfile` | `npm run dev` no compose |
| `worker` | `backend/Dockerfile` | `run_export_worker` |

## Persistência

- `db_data`: dados PostgreSQL;
- `backend_static`: estáticos do backend;
- código backend/frontend montado para desenvolvimento.

Arquivos de mídia não possuem volume dedicado no compose analisado. Para dados relevantes, configure storage persistente.

## Rede e portas

- banco: `127.0.0.1:5432`;
- backend: `8000`;
- frontend: `3000`.

O frontend recebe `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/`, pois o navegador acessa a porta publicada no host.

## Produção

Não use o compose local como definição de produção: ele executa `runserver`, monta código fonte e não define TLS, réplicas, secret manager, backup ou observabilidade.

[Voltar](README.md)
