# Diagnóstico de runtime do módulo de Comunicações

## Endpoints retornam 500 ou 503

Quando dashboard, comunicações, templates, automações, canais e notificações falham ao mesmo tempo, verifique primeiro:

- migrations;
- PostgreSQL;
- Redis;
- backend;
- worker `communications`;
- Celery Beat;
- organização ativa e permissions.

## Ambiente Docker Compose

```bash
docker compose exec backend python manage.py showmigrations communications
docker compose exec backend python manage.py migrate --noinput
docker compose restart backend celery-worker-communications celery-beat
```

Para recriar os serviços após mudança de Dockerfile, requirements ou Compose:

```bash
docker compose up -d --build backend celery-worker-communications celery-beat
```

Verifique logs:

```bash
docker compose logs --tail=200 backend
docker compose logs --tail=200 celery-worker-communications
docker compose logs --tail=200 celery-beat
docker compose logs --tail=200 redis
docker compose logs --tail=200 db
```

## Backend executado fora do Docker

```bash
cd backend
python manage.py showmigrations communications
python manage.py migrate --noinput
python manage.py check
```

Em terminais separados:

```bash
celery -A config worker --loglevel=INFO --queues=communications --concurrency=2
celery -A config beat --loglevel=INFO
python manage.py runserver
```

## Resposta `COMMUNICATIONS_DATABASE_NOT_READY`

O backend pode converter falhas de banco em `503 Service Unavailable` com código controlado. Isso evita stack trace público, mas não identifica sozinho a causa.

Investigue:

- migration pendente;
- PostgreSQL indisponível;
- conexão ou senha divergente;
- lock ou timeout;
- organização/contexto inválido;
- deploy parcial.

## Comunicação permanece pendente

Verifique:

1. `COMMUNICATIONS_ENABLED`;
2. status persistido;
3. worker `celery-worker-communications`;
4. Beat e tarefa `communications-dispatch-due`;
5. Redis;
6. tentativas e próximo retry;
7. consentimento, opt-out e janela de envio;
8. entitlement;
9. provider e credenciais.

O health check do worker não comprova SMTP, WhatsApp ou SMS saudáveis.

## Automação não dispara

Verifique o Beat e a tarefa:

```text
apps.communications.tasks.schedule_operational_automations
```

Frequência padrão: 300 segundos, configurável por `COMMUNICATIONS_AUTOMATION_INTERVAL_SECONDS`.

Mantenha apenas uma instância de Beat sem coordenação adicional.

## WhatsApp manual

Abertura do link `wa.me` não significa envio, entrega ou leitura. O status depende da confirmação humana prevista no fluxo.

## Verificação rápida

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest apps/communications/tests -q
```

Frontend:

```bash
cd frontend
node --experimental-strip-types --test communications.test.mjs
npm run lint
npm run typecheck
```

## Endpoints de smoke test

Com sessão e tenant válidos:

```text
GET /api/v1/communications/notifications/unread-count/
GET /api/v1/communications/channels/
GET /api/v1/communications/templates/
```

Não use dados reais em smoke tests de desenvolvimento ou CI.

## Logs

Procure pelo `X-Request-ID`, public ID da comunicação, task ID e organização. Não registre corpo, token público, credencial, telefone ou e-mail completo.

Avisos de fontes do Next.js ou mensagens de extensão do navegador não explicam, por si só, falhas HTTP do backend. Priorize status, request ID e logs sanitizados dos serviços envolvidos.

[Voltar ao módulo](README.md)
