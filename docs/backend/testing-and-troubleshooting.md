# Testes, qualidade e troubleshooting

> Esta página permanece para compatibilidade com links antigos. Use as referências canônicas:
>
> - [Testes e qualidade](../10-testes/README.md);
> - [Docker e workers](../12-operacao/docker-e-workers.md);
> - [Instalação com Docker](../03-instalacao/instalacao-docker.md);
> - [Variáveis de ambiente](../04-configuracao/variaveis-de-ambiente.md).

## Verificações principais do backend

```bash
cd backend
python apps/core/quality/check_backend_architecture.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file schema.yml --validate
ruff check .
mypy .
pytest --create-db
```

Não altere testes, permissions ou regras de negócio apenas para obter resultado verde. Corrija a causa ou registre a limitação real.

## Verificações do frontend

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run test:coverage
npm run test:auth
npm run build
```

## Docker

```bash
docker compose config
docker compose config --services
docker compose ps
docker compose logs backend
docker compose logs frontend
docker compose logs db
docker compose logs redis
docker compose logs celery-worker-default
docker compose logs celery-worker-exports
docker compose logs celery-worker-uploads
docker compose logs celery-worker-communications
docker compose logs celery-beat
```

Checks pontuais:

```bash
docker compose exec backend python manage.py check
docker compose exec backend pytest --create-db
docker compose exec backend python manage.py makemigrations --check --dry-run
```

## Cenários prioritários

### Multi-tenancy

Teste com pelo menos dois usuários e duas organizações:

- pacientes;
- prontuário;
- agenda;
- financeiro;
- documentos;
- formulários;
- Billing;
- comunicações;
- relatórios;
- exportações;
- downloads;
- tasks Celery;
- cache após troca de organização.

### Concorrência

Use PostgreSQL para validar:

- sequência documental;
- consumo de pacote;
- recorrência;
- confirmação de pagamento;
- webhook duplicado;
- reserva de exportação;
- scan de upload;
- reprocessamento de comunicação.

SQLite não reproduz todos os locks e constraints do PostgreSQL.

### Segurança

Priorize:

- enumeração de conta;
- token expirado ou revogado;
- lockout;
- organização sem membership;
- relações cruzadas;
- evolução confidencial;
- upload inválido;
- download sem autorização;
- webhook sem autenticação;
- idempotência;
- ausência de segredos em logs e artefatos.

## Problemas comuns

### Settings ou secret ausente

Confirme qual arquivo de ambiente pertence ao processo:

- Compose: `.env` na raiz;
- backend direto: `backend/.env`;
- frontend direto: `frontend/.env.local`.

Use valores distintos para Django, JWT, criptografia e webhook.

### Banco indisponível

```bash
docker compose ps db
docker compose logs db
```

Dentro do Docker, o hostname é `db`, não `localhost`.

### Redis indisponível

```bash
docker compose ps redis
docker compose logs redis
```

A indisponibilidade afeta Celery, cache e rate limit de produção.

### Erro 401, 403 ou 404

Verifique sessão, CSRF, assinatura, membership, organização ativa, papel, ownership, confidencialidade e entitlement. Um `404` pode ser a resposta correta para ocultar recurso de outro tenant.

### Exportação presa

Verifique `celery-worker-exports`, Celery Beat, timeout, storage e registro persistido.

### Upload sem avançar

Verifique `celery-worker-uploads`, dispatcher, recuperação, status de rejeição e storage. Não presuma provider antimalware externo ativo.

### Comunicação não enviada

Verifique `celery-worker-communications`, Beat, canal, consentimento, opt-out, entitlement, tentativas e provider.

### Checkout ou webhook Asaas

Verifique feature, API key, base URL, token, evento persistido, worker `default` e reconciliação. Não imprima credenciais.

### Telemedicina indisponível

Verifique LiveKit, HTTPS/WSS, webhook, consentimento, E2EE, horário e manutenção na fila `default`.

## Antes do Pull Request

- [ ] arquitetura verificada;
- [ ] migrations verificadas;
- [ ] testes relevantes executados;
- [ ] Ruff e mypy avaliados;
- [ ] frontend lint, typecheck e build avaliados;
- [ ] OpenAPI validado;
- [ ] documentação atualizada;
- [ ] nenhum segredo no diff;
- [ ] nenhuma regra funcional alterada por tarefa documental.
