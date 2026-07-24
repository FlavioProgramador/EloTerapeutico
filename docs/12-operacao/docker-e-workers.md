# Operação de Docker e workers

Este runbook é destinado a desenvolvimento, suporte técnico e operação. Não use comandos destrutivos sem confirmar ambiente, impacto e backup.

## Diagnóstico inicial

Na raiz:

```bash
docker compose config --services
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 redis
docker compose logs --tail=100 db
```

Serviços esperados:

```text
db
redis
backend
frontend
celery-worker-exports
celery-worker-uploads
celery-worker-communications
celery-worker-default
celery-beat
```

Se um nome não aparecer, valide a versão do repositório e o `docker-compose.yml` usado.

## Health checks

### Backend

```bash
curl -fsS http://localhost:8000/health/live/
curl -fsS http://localhost:8000/health/ready/
```

- `live` indica que o processo responde;
- `ready` verifica dependências configuradas;
- sucesso não comprova integrações externas saudáveis.

### PostgreSQL

```bash
docker compose exec db pg_isready -U "${POSTGRES_USER:-postgres}"
```

### Redis

```bash
docker compose exec redis sh -c 'redis-cli -a "$REDIS_PASSWORD" ping'
```

Não copie a senha para tickets, screenshots ou logs públicos.

### Workers

```bash
docker compose exec celery-worker-default celery -A config inspect ping
docker compose exec celery-worker-exports celery -A config inspect ping
docker compose exec celery-worker-uploads celery -A config inspect ping
docker compose exec celery-worker-communications celery -A config inspect ping
```

`inspect ping` confirma resposta dos workers acessíveis, mas não garante que a fila esteja sem backlog ou que providers estejam disponíveis.

## Backend indisponível

1. confirme `db` e `redis` saudáveis;
2. veja logs do backend;
3. valide settings e migrations;
4. confira secrets e URLs;
5. não desative controles de segurança para iniciar.

```bash
docker compose logs --tail=300 backend
docker compose exec backend python manage.py check
docker compose exec backend python manage.py showmigrations
docker compose exec backend python manage.py makemigrations --check --dry-run
```

Se migrations falharem, preserve o erro completo apenas em canal técnico autorizado e sanitize valores sensíveis antes de compartilhar.

## Frontend sem comunicação com backend

Verifique:

```bash
docker compose logs --tail=200 frontend
docker compose ps backend frontend
```

Configuração esperada no Compose:

```text
BACKEND_API_URL=http://backend:8000/api/v1/
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/
```

Causas comuns:

- backend não ready;
- URL interna usando `localhost` dentro do container;
- CORS ou CSRF divergente;
- cookies bloqueados por domínio ou segurança;
- BFF retornando falha sanitizada do upstream;
- organização ativa inválida.

## Erro de autenticação, CSRF ou tenant

Antes de alterar código:

- confirme origem do frontend;
- confirme `CSRF_TRUSTED_ORIGINS`;
- confirme cookies de sessão;
- confirme que a requisição passa pelo BFF;
- confirme membership ativa;
- confirme `X-Organization-ID` quando exigido;
- confirme organização ativa e não suspensa.

Nunca contorne CSRF, CORS ou permissions para resolver temporariamente.

## PostgreSQL indisponível

```bash
docker compose logs --tail=200 db
docker compose exec db pg_isready -U "${POSTGRES_USER:-postgres}"
docker compose restart db
```

Após reiniciar, verifique backend e workers. Tasks podem voltar a tentar operações e precisam manter idempotência.

Riscos:

- locks longos;
- conexões esgotadas;
- disco cheio;
- migration incompatível;
- volume corrompido;
- senha divergente da `DATABASE_URL`.

## Redis indisponível

```bash
docker compose logs --tail=200 redis
docker compose restart redis
```

Impactos possíveis:

- publicação de tasks;
- execução assíncrona;
- resultados temporários;
- cache;
- rate limiting em produção.

Estados persistidos de exportações, uploads, comunicações e webhooks devem continuar no PostgreSQL e ser recuperados pelos dispatchers.

## Worker parado

Exemplo para comunicações:

```bash
docker compose logs --tail=200 celery-worker-communications
docker compose restart celery-worker-communications
docker compose exec celery-worker-communications celery -A config inspect ping
```

Repita com o serviço afetado.

Verifique:

- Redis;
- PostgreSQL;
- import de settings;
- nome da fila;
- dependências;
- time limit;
- erro de provider;
- OOM ou encerramento forçado.

## Jobs presos

Jobs persistidos devem possuir timeout e rotina de recuperação.

### Exportações

Monitore registros pendentes ou em processamento por tempo superior a `CLINICAL_EXPORT_PROCESSING_TIMEOUT_MINUTES`. O Beat publica dispatcher, recuperação e expiração na fila `exports`.

### Uploads

Monitore scans presos, rejeitados e backlog. O Beat publica dispatcher e recuperação na fila `uploads`.

### Comunicações

Monitore status `processing`, número de tentativas e próximo retry. O timeout é controlado por `COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES`.

### Webhooks de Billing

Monitore eventos pendentes, em retry e failed. Reconciliação deve corrigir divergências sem duplicar cobrança.

Não altere status diretamente no banco sem entender as constraints e a idempotência do fluxo.

## Celery Beat parado

```bash
docker compose logs --tail=200 celery-beat
docker compose restart celery-beat
```

Verifique PID, schedule e acesso ao Redis.

> Mantenha apenas uma instância sem coordenação adicional. Múltiplos Beats podem publicar tarefas duplicadas.

## Filas e responsabilidades

| Fila | Serviço | Sintoma quando parada |
| --- | --- | --- |
| `default` | `celery-worker-default` | webhooks, reconciliação e manutenção atrasados |
| `exports` | `celery-worker-exports` | exportações permanecem pendentes |
| `uploads` | `celery-worker-uploads` | documentos aguardam verificação |
| `communications` | `celery-worker-communications` | notificações e mensagens não avançam |

## Falha de Azure Blob

Verifique:

- `AZURE_STORAGE_CONNECTION_STRING`;
- `AZURE_CONTAINER_NAME`;
- container privado;
- expiração de URL;
- rede e permissão;
- `PRIVATE_MEDIA_STORAGE_REQUIRED`;
- health de storage quando habilitado.

Não mude para container público. Não faça fallback silencioso para disco efêmero em produção.

## Falha de Asaas

Verifique:

- feature de Billing;
- API key;
- base URL;
- token do webhook;
- timeout;
- evento persistido;
- retries;
- reconciliação.

Produção não aceita URL de sandbox. Não registre payload integral ou API key.

## Webhook inválido

- preserve resposta genérica;
- valide assinatura/token;
- não processe evento não autenticado;
- registre somente identificadores e motivo sanitizado;
- confirme idempotência;
- não repita manualmente sem verificar se o evento já foi aplicado.

## LiveKit indisponível

Verifique:

- `TELEMEDICINE_ENABLED`;
- `LIVEKIT_URL` com `wss://`;
- API key e secret;
- HTTPS do frontend;
- webhook;
- horário da consulta;
- consentimento;
- E2EE;
- limite de participantes.

Não desative E2EE ou aumente TTL para mascarar erro de configuração.

## SMTP indisponível

Verifique host, porta, usuário, senha, TLS, remetente e reputação. Desenvolvimento usa console e não comprova entrega real.

Links temporários não devem aparecer em logs de suporte.

## Comunicação não enviada

Verifique:

- `COMMUNICATIONS_ENABLED`;
- worker e Beat;
- canal configurado;
- destinatário válido;
- consentimento e opt-out;
- janela de envio;
- entitlement;
- número de tentativas;
- erro sanitizado;
- provider externo.

WhatsApp manual exige confirmação humana; abertura do link não equivale a envio.

## Logs seguros

Logs podem conter:

- request ID;
- organization ID;
- user ID técnico;
- public ID do recurso;
- task ID;
- status;
- duração;
- classe de erro sanitizada.

Logs não devem conter:

- prontuário;
- diagnóstico;
- anamnese;
- evolução;
- documento;
- senha;
- JWT;
- refresh token;
- chave E2EE;
- API key;
- connection string;
- token público;
- telefone ou e-mail completo.

## Backup e restauração

Antes de operações destrutivas:

1. identifique o ambiente;
2. confirme escopo;
3. gere backup;
4. proteja e criptografe o arquivo;
5. teste restauração em ambiente descartável;
6. registre responsável, data e resultado.

`docker compose down -v` destrói os volumes locais.

## Pós-deploy

Após implantação controlada:

1. validar migrations;
2. validar liveness e readiness;
3. validar frontend e BFF;
4. validar autenticação e tenant;
5. confirmar workers e Beat;
6. testar storage privado;
7. executar smoke tests de integrações configuradas;
8. confirmar logs e métricas;
9. confirmar backup;
10. manter plano de rollback.

## Escalonamento

Acione engenharia ou segurança quando houver:

- possível acesso cruzado entre organizações;
- vazamento de token ou segredo;
- arquivo clínico público;
- webhook não autenticado aplicado;
- perda ou corrupção de dados;
- backup sem restauração possível;
- logs com conteúdo clínico;
- repetição de cobrança;
- gravação ou transmissão de mídia fora do esperado.

[Voltar à operação](README.md)
