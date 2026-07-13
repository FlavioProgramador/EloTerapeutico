# Diagnóstico de runtime do módulo de Comunicações

## Todos os endpoints retornam 500 ou 503

Quando `communications/`, `templates/`, `automations/`, `channels/`, `dashboard/` e `notifications/unread-count/` falham ao mesmo tempo, a causa mais comum é o banco local ainda não possuir as migrations do app `communications`.

Isso pode acontecer quando o código é atualizado enquanto o `runserver` ou os containers já estão em execução. O autoreload carrega o novo código, mas não executa migrations automaticamente.

### Ambiente Docker Compose

```bash
docker compose exec backend python manage.py showmigrations communications
docker compose exec backend python manage.py migrate --noinput
docker compose restart backend communications-worker communications-scheduler
```

Para recriar os serviços após mudanças no Compose:

```bash
docker compose up -d --build backend communications-worker communications-scheduler
```

### Backend executado fora do Docker

```bash
cd backend
python manage.py showmigrations communications
python manage.py migrate --noinput
python manage.py runserver
```

Todas as migrations `0001` até `0007` devem aparecer marcadas com `[X]`.

## Resposta `COMMUNICATIONS_DATABASE_NOT_READY`

O backend converte falhas de banco dentro das views de Comunicações em HTTP `503 Service Unavailable` com o código:

```text
COMMUNICATIONS_DATABASE_NOT_READY
```

Essa resposta evita múltiplos erros genéricos `500` e indica que as migrations precisam ser aplicadas ou que o banco está temporariamente indisponível.

## Verificação rápida

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest apps/communications/tests -q
```

Depois da migração, teste:

```text
GET /api/v1/communications/notifications/unread-count/
GET /api/v1/communications/channels/
GET /api/v1/communications/templates/
```

## Mensagens que não são a causa principal

- avisos de fontes `.woff2` pré-carregadas e não utilizadas são warnings de otimização do Next.js;
- `Não é possível adicionar o sistema de arquivos: <illegal path>` costuma vir do navegador, DevTools ou extensão e não explica os erros HTTP do backend;
- o bloqueio real deve ser investigado pelo status HTTP e pelo `X-Request-ID` retornado pela API.
