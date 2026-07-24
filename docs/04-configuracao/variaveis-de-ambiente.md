# Variáveis de ambiente

Esta referência compara `.env.example`, `backend/.env.example`, `frontend/.env.example`, settings Django, Docker Compose e Dockerfiles.

## Arquivos e escopo

| Arquivo | Uso | Regra |
| --- | --- | --- |
| `.env.example` | Ambiente canônico do Docker Compose | Copie para `.env` na raiz; backend, workers, Beat, banco e Redis recebem essas variáveis |
| `backend/.env.example` | Backend executado diretamente fora do Docker | Copie para `backend/.env`; pode usar SQLite ou PostgreSQL local |
| `frontend/.env.example` | Frontend e BFF | Copie para `frontend/.env.local` quando executar Next.js diretamente |
| `.env` | Configuração local real do Compose | Não versionar |
| `backend/.env` | Configuração local real do Django fora do Compose | Não versionar |
| `frontend/.env.local` | Configuração local real do Next.js | Não versionar |

`django-environ` não sobrescreve variáveis já injetadas no processo. No Compose, use o `.env` da raiz como fonte canônica e evite manter valores divergentes em múltiplos arquivos.

## Classificação

- **Obrigatória:** processo não deve iniciar sem valor válido no ambiente indicado;
- **Condicional:** exigida quando uma feature ou integração é ativada;
- **Opcional:** possui default adequado ao ambiente local;
- **Sensível:** deve ficar em secret manager na produção.

## Django e rede

| Variável | Componente | Obrigatória | Ambiente | Exemplo seguro | Sensível | Finalidade |
| --- | --- | --- | --- | --- | ---: | --- |
| `DJANGO_SETTINGS_MODULE` | Backend/workers | Sim | Todos | `config.settings.development` | Não | Seleciona settings |
| `SECRET_KEY` | Django | Sim | Todos | `configure-segredo-distinto` | Sim | Assinaturas internas Django |
| `DEBUG` | Django | Não | Dev | `True` | Não | Debug local |
| `ALLOWED_HOSTS` | Django | Sim em prod | Todos | `api.example.test` | Não | Hosts aceitos |
| `FRONTEND_URL` | Backend | Sim em prod | Todos | `https://app.example.test` | Não | Links e origem da aplicação |
| `CORS_ALLOWED_ORIGINS` | Backend | Sim em prod | Todos | `https://app.example.test` | Não | Origens CORS |
| `CSRF_TRUSTED_ORIGINS` | Backend | Conforme topologia | Todos | `https://app.example.test` | Não | Origens confiáveis para CSRF |
| `TRUST_PROXY_CLIENT_IP_HEADERS` | Backend | Não | Prod | `False` | Não | Confiar em headers de IP do proxy |
| `HEALTH_CHECK_STORAGE` | Backend | Não | Prod | `False` | Não | Incluir storage no readiness |
| `PASSWORD_RESET_TIMEOUT` | Backend | Não | Todos | `900` | Não | Validade do reset em segundos |

## SQL Explorer administrativo

O SQL Explorer é desativado por padrão e proibido em produção.

| Variável | Obrigatória | Ambiente | Default | Sensível | Finalidade |
| --- | --- | --- | --- | ---: | --- |
| `ADMIN_SQL_EXPLORER_ENABLED` | Não | Dev autorizado | `False` | Não | Habilitar interface administrativa |
| `ADMIN_SQL_EXPLORER_DATABASE_ALIAS` | Não | Dev | `default` | Não | Alias do banco |
| `ADMIN_SQL_EXPLORER_MAX_ROWS` | Não | Dev | `100` | Não | Limite de linhas |
| `ADMIN_SQL_EXPLORER_TIMEOUT_MS` | Não | Dev | `2000` | Não | Timeout da consulta |
| `ADMIN_SQL_EXPLORER_ALLOWED_TABLES` | Não | Dev | `django_migrations` | Pode ser | Allowlist mínima de tabelas |

## PostgreSQL

| Variável | Componente | Obrigatória | Ambiente | Exemplo seguro | Sensível | Finalidade |
| --- | --- | --- | --- | --- | ---: | --- |
| `DATABASE_URL` | Backend/workers | Sim | Todos | `postgres://usuario:senha@db:5432/config` | Sim | Conexão principal |
| `POSTGRES_DB` | Container `db` | Sim no Compose | Dev | `config` | Não | Nome do banco |
| `POSTGRES_USER` | Container `db` | Sim no Compose | Dev | `postgres` | Não | Usuário |
| `POSTGRES_PASSWORD` | Container `db` | Sim no Compose | Dev | `configure-senha-local` | Sim | Senha |
| `POSTGRES_HOST` | Backend direto | Não | Dev | `localhost` | Não | Host auxiliar |
| `POSTGRES_PORT` | Backend direto | Não | Dev | `5432` | Não | Porta auxiliar |

Dentro do Compose, use hostname `db`. Fora do Docker, use `localhost` ou a URL do serviço remoto.

## Redis e Celery

| Variável | Obrigatória | Ambiente | Default/exemplo | Sensível | Finalidade |
| --- | --- | --- | --- | ---: | --- |
| `REDIS_PASSWORD` | Compose | Sim | `configure-senha-local-redis` | Sim | Autenticação Redis |
| `REDIS_URL` | Sim em prod | Todos | `redis://:senha@redis:6379/0` | Sim | Cache e fallback do broker |
| `REDIS_RESULT_URL` | Sim em prod | Todos | `redis://:senha@redis:6379/1` | Sim | Result backend |
| `CELERY_BROKER_URL` | Sim | Dev/prod | URL Redis `/0` | Sim | Broker |
| `CELERY_RESULT_BACKEND` | Sim | Dev/prod | URL Redis `/1` | Sim | Resultados temporários |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | Não | Dev/prod | `1` | Não | Prefetch por processo |
| `CELERY_VISIBILITY_TIMEOUT_SECONDS` | Não | Dev/prod | `3600` | Não | Tempo para mensagem não confirmada voltar |
| `CELERY_RESULT_EXPIRES_SECONDS` | Não | Dev/prod | `3600` | Não | Retenção de resultados |
| `CELERY_TASK_SOFT_TIME_LIMIT_SECONDS` | Não | Dev/prod | `300` | Não | Soft time limit |
| `CELERY_TASK_TIME_LIMIT_SECONDS` | Não | Dev/prod | `360` | Não | Hard time limit |
| `CELERY_DEFAULT_CONCURRENCY` | Não | Compose | `1` | Não | Concorrência do worker `default` |
| `CELERY_EXPORT_CONCURRENCY` | Não | Compose | `1` | Não | Concorrência do worker `exports` |
| `CELERY_UPLOADS_CONCURRENCY` | Não | Compose | `1` | Não | Concorrência do worker `uploads` |
| `CELERY_COMMUNICATIONS_CONCURRENCY` | Não | Compose | `2` | Não | Concorrência do worker `communications` |

O `.env.example` da raiz deve conter todas as variáveis de concorrência usadas pelo Compose. Uma ausência pode fazer o default do Compose funcionar, mas reduz a clareza operacional.

## Exportações clínicas

| Variável | Default | Finalidade |
| --- | --- | --- |
| `CLINICAL_EXPORT_DISPATCH_BATCH_SIZE` | `20` | Quantidade reservada por dispatcher |
| `CLINICAL_EXPORT_PROCESSING_TIMEOUT_MINUTES` | `15` | Detecção de job preso |
| `CLINICAL_EXPORT_MAX_RETRIES` | `3` | Limite de retries |
| `CLINICAL_EXPORT_RETENTION_HOURS` | `24` | Retenção do arquivo exportado |
| `EXPORT_DISPATCH_INTERVAL_SECONDS` | `10` | Frequência do dispatcher |
| `EXPORT_RECOVERY_INTERVAL_SECONDS` | `300` | Frequência de recuperação |

## Verificação de uploads clínicos

| Variável | Obrigatória | Default | Finalidade |
| --- | --- | --- | --- |
| `CLINICAL_SCAN_DISPATCH_INTERVAL_SECONDS` | Não | `20` no settings | Dispatcher de scans pendentes |
| `CLINICAL_SCAN_RECOVERY_INTERVAL_SECONDS` | Não | `120` no settings | Recuperação de scans presos |

Outras variáveis específicas do provider antimalware só devem ser documentadas quando existirem no código. A fila `uploads` não comprova provider externo ativo.

## JWT e criptografia

| Variável | Obrigatória | Ambiente | Exemplo seguro | Sensível | Finalidade |
| --- | --- | --- | --- | ---: | --- |
| `JWT_SECRET` | Sim | Todos | `configure-segredo-jwt-distinto` | Sim | Assinatura JWT |
| `JWT_ACCESS_MINUTES` | Não | Todos | `30` | Não | Vida do access token |
| `JWT_REFRESH_DAYS` | Não | Todos | `7` | Não | Vida do refresh token |
| `FIELD_ENCRYPTION_KEY` | Sim | Todos | `configure-chave-de-dados` | Sim | Criptografia de campos |
| `FIELD_ENCRYPTION_KEY_V2` | Durante rotação | Todos | `configure-chave-nova` | Sim | Nova versão da chave |

Em produção, `SECRET_KEY`, `JWT_SECRET`, `FIELD_ENCRYPTION_KEY` e `ASAAS_WEBHOOK_TOKEN` devem ser fortes e distintos.

## Frontend e BFF

| Variável | Componente | Obrigatória | Ambiente | Exemplo seguro | Sensível | Finalidade |
| --- | --- | --- | --- | --- | ---: | --- |
| `BACKEND_API_URL` | Servidor Next.js | Sim | Todos | `http://backend:8000/api/v1/` | Pode conter rede interna | URL server-side do backend |
| `NEXT_PUBLIC_API_URL` | Browser/frontend | Sim | Dev | `http://localhost:8000/api/v1/` | Não pode ser | Fallback público |
| `AUTH_ACCESS_COOKIE_MAX_AGE` | BFF | Não | Todos | `1800` | Não | Expiração do cookie access |
| `AUTH_REFRESH_COOKIE_MAX_AGE` | BFF | Não | Todos | `604800` | Não | Expiração do cookie refresh |
| `LIVEKIT_URL` | Frontend/telemedicina | Condicional | Dev/prod | `wss://livekit.example.test` | Não | Endpoint WebSocket LiveKit |

Variáveis `NEXT_PUBLIC_*` entram no bundle. Nunca use esse prefixo para tokens, senhas, connection strings ou chaves privadas.

## Telemedicina e LiveKit

| Variável | Obrigatória | Default | Sensível | Finalidade |
| --- | --- | --- | ---: | --- |
| `TELEMEDICINE_ENABLED` | Não | `False` | Não | Feature flag operacional |
| `TELEMEDICINE_PROVIDER` | Quando ativa | `livekit` | Não | Provider de mídia |
| `LIVEKIT_URL` | Quando ativa | vazio | Não | Endpoint WSS/API |
| `LIVEKIT_API_KEY` | Quando ativa | vazio | Sim | Credencial LiveKit |
| `LIVEKIT_API_SECRET` | Quando ativa | vazio | Sim | Segredo LiveKit |
| `TELEMEDICINE_REQUIRE_E2EE` | Não | `True` | Não | Exigir E2EE |
| `TELEMEDICINE_JOIN_BEFORE_MINUTES` | Não | `15` | Não | Entrada antes do horário |
| `TELEMEDICINE_JOIN_AFTER_MINUTES` | Não | `30` | Não | Entrada após o horário |
| `TELEMEDICINE_PROVIDER_TOKEN_TTL_SECONDS` | Não | `300` | Não | TTL do token do provider |
| `TELEMEDICINE_EMPTY_ROOM_TIMEOUT_SECONDS` | Não | `300` | Não | Timeout de sala vazia |
| `TELEMEDICINE_MAX_PARTICIPANTS` | Não | `2` | Não | Limite de participantes |
| `TELEMEDICINE_MAINTENANCE_INTERVAL_SECONDS` | Não | `300` | Não | Frequência de manutenção |

Ativar a flag sem credenciais, HTTPS/WSS e webhook não torna a integração operacional.

## Azure Blob e mídia privada

| Variável | Obrigatória | Ambiente | Default | Sensível | Finalidade |
| --- | --- | --- | --- | ---: | --- |
| `AZURE_STORAGE_CONNECTION_STRING` | Condicional | Prod | vazio | Sim | Acesso ao Blob |
| `AZURE_CONTAINER_NAME` | Condicional | Dev/prod | `elo-terapeutico` | Não | Nome do container |
| `AZURE_URL_EXPIRATION_SECS` | Não | Prod | `300` | Não | Expiração de URLs |
| `PRIVATE_MEDIA_STORAGE_REQUIRED` | Sim para política segura | Prod | `True` em settings de produção | Não | Impedir filesystem efêmero |

O repositório não comprova conta ou container implantado.

## Documentos institucionais

| Variável | Obrigatória | Default | Sensível | Finalidade |
| --- | --- | --- | ---: | --- |
| `DOCUMENT_CLINIC_NAME` | Não | `Elo Terapêutico` | Não | Nome em documentos |
| `DOCUMENT_CLINIC_ADDRESS` | Não | vazio | Pode ser | Endereço institucional |
| `DOCUMENT_CLINIC_PHONE` | Não | vazio | Pode ser | Telefone institucional |

Configurações por organização podem substituir valores globais conforme o fluxo implementado.

## Billing e Asaas

| Variável | Obrigatória | Default | Sensível | Finalidade |
| --- | --- | --- | ---: | --- |
| `BILLING_ENABLED` | Não | `True` no exemplo raiz | Não | Habilitar domínio comercial |
| `ASAAS_API_KEY` | Sim em prod | vazio | Sim | API Asaas |
| `ASAAS_BASE_URL` | Sim | sandbox local | Não | Endpoint do gateway |
| `ASAAS_WEBHOOK_TOKEN` | Sim em prod | placeholder local | Sim | Autenticar webhook |
| `BILLING_TRIAL_DAYS` | Não | `7` | Não | Período de teste |
| `BILLING_DEFAULT_CURRENCY` | Não | `BRL` | Não | Moeda |
| `BILLING_GRACE_PERIOD_DAYS` | Não | `5` | Não | Carência |
| `BILLING_MAX_INSTALLMENTS` | Não | `12` | Não | Parcelas máximas |
| `BILLING_WEBHOOK_MAX_RETRIES` | Não | `5` | Não | Retentativas de webhook |
| `BILLING_WEBHOOK_DISPATCH_BATCH_SIZE` | Não | `50` | Não | Lote do dispatcher |
| `BILLING_WEBHOOK_RESERVATION_TIMEOUT_MINUTES` | Não | `5` | Não | Reserva de evento |
| `BILLING_WEBHOOK_DISPATCH_INTERVAL_SECONDS` | Não | `15` | Não | Frequência do dispatcher |
| `BILLING_WEBHOOK_PROCESS_INLINE` | Não | `False` no Compose | Não | Processamento inline apenas em testes/dev controlado |
| `BILLING_RECONCILIATION_ENABLED` | Não | `True` | Não | Ativar reconciliação |
| `BILLING_RECONCILIATION_INTERVAL_MINUTES` | Não | `60` | Não | Frequência de reconciliação |
| `BILLING_RECONCILIATION_BATCH_SIZE` | Não | `50` | Não | Lote de reconciliação |
| `BILLING_CHECKOUT_EXPIRATION_MINUTES` | Não | `30` | Não | Validade do checkout |

Produção rejeita `ASAAS_BASE_URL` de sandbox.

## E-mail

| Variável | Obrigatória | Ambiente | Default/exemplo | Sensível | Finalidade |
| --- | --- | --- | --- | ---: | --- |
| `EMAIL_BACKEND` | Não | Dev | console backend | Não | Implementação Django de e-mail |
| `DEFAULT_FROM_EMAIL` | Sim em prod | Todos | `noreply@example.test` | Não | Remetente |
| `EMAIL_HOST` | Sim em prod | Prod | `smtp.sendgrid.net` em settings | Não | Host SMTP |
| `EMAIL_PORT` | Não | Prod | `587` | Não | Porta |
| `EMAIL_HOST_USER` | Sim em prod | Prod | vazio | Sim | Usuário SMTP |
| `EMAIL_HOST_PASSWORD` | Sim em prod | Prod | vazio | Sim | Senha SMTP |
| `EMAIL_USE_TLS` | Não | Prod | `True` | Não | TLS |
| `EMAIL_TIMEOUT` | Não | Todos | `15` | Não | Timeout |

## Comunicações

| Variável | Default | Finalidade |
| --- | --- | --- |
| `COMMUNICATIONS_ENABLED` | `True` | Habilitar o módulo |
| `COMMUNICATIONS_BATCH_SIZE` | `50` | Lote de processamento |
| `COMMUNICATIONS_MAX_ATTEMPTS` | `5` | Tentativas máximas |
| `COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES` | `15` | Recuperação de registros presos |
| `COMMUNICATIONS_DEFAULT_TIMEZONE` | `America/Sao_Paulo` | Timezone operacional |
| `COMMUNICATIONS_REPLY_TO` | vazio | Reply-To padrão |
| `COMMUNICATIONS_DISPATCH_INTERVAL_SECONDS` | `20` | Frequência do dispatcher |
| `COMMUNICATIONS_AUTOMATION_INTERVAL_SECONDS` | `300` | Frequência das automações |
| `COMMUNICATIONS_PAYMENT_DUE_DAYS` | `3` | Janela de vencimento |
| `COMMUNICATIONS_FORM_REMINDER_HOURS` | `24` | Lembrete de formulário |
| `COMMUNICATIONS_DOCUMENT_REMINDER_HOURS` | `24` | Lembrete de documento |
| `COMMUNICATIONS_TOKEN_RETENTION_DAYS` | `90` | Retenção técnica de tokens |

## WhatsApp Business

| Variável | Obrigatória quando ativa | Sensível | Finalidade |
| --- | ---: | ---: | --- |
| `WHATSAPP_PROVIDER` | Sim | Não | Provider selecionado |
| `WHATSAPP_API_BASE_URL` | Sim | Não | Endpoint |
| `WHATSAPP_ACCESS_TOKEN` | Sim | Sim | Token |
| `WHATSAPP_PHONE_NUMBER_ID` | Sim | Pode ser | Número do provider |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Sim | Sim | Verificação inicial do webhook |
| `WHATSAPP_APP_SECRET` | Sim | Sim | Assinatura do webhook |

Deixar variáveis vazias mantém o canal inativo. Configurar valores sem implementar/validar o provider não comprova operação.

## SMS

| Variável | Obrigatória quando ativa | Sensível | Finalidade |
| --- | ---: | ---: | --- |
| `SMS_PROVIDER` | Sim | Não | Provider selecionado |
| `SMS_API_KEY` | Sim | Sim | Credencial |
| `SMS_SENDER` | Sim | Pode ser | Remetente |

## CI e testes

Workflows podem definir variáveis sintéticas para PostgreSQL, Django, BFF, E2E, Billing e coverage. Regras:

- usar apenas dados sintéticos;
- não imprimir cookies ou tokens;
- não enviar `.env` como artefato;
- usar secrets do GitHub para valores protegidos;
- não reutilizar credenciais de produção.

## Precedência e consistência

1. variável injetada no processo;
2. `.env` lido pelo componente;
3. default do settings ou Compose;
4. ausência, quando permitida.

Ao alterar uma variável:

- atualize settings e Compose;
- atualize o `.env.example` correto;
- atualize esta referência;
- revise Dockerfiles e workflows;
- adicione validação quando a divergência puder quebrar o ambiente.

## Segurança

- não versione `.env` real;
- não documente valores reais;
- não coloque segredos em `NEXT_PUBLIC_*`;
- não reutilize secrets entre Django, JWT, criptografia e webhooks;
- não publique a saída expandida de `docker compose config`;
- prefira Key Vault ou mecanismo equivalente em produção;
- planeje rotação de chaves sem perder dados criptografados.


## Headers defensivos e correlação

| Variável | Componente | Obrigatória | Finalidade |
| --- | --- | --- | --- |
| `SECURITY_PERMISSIONS_POLICY` | backend | Não | Define recursos de navegador permitidos. O padrão bloqueia câmera, microfone, geolocalização, pagamentos e USB. |
| `SECURITY_CROSS_ORIGIN_RESOURCE_POLICY` | backend | Não | Define `Cross-Origin-Resource-Policy`; o padrão é `same-site`. |
| `SECURITY_CONTENT_SECURITY_POLICY` | backend | Produção | Define a CSP. Produção possui padrão restritivo e deve permitir somente os domínios realmente utilizados. |

Todas as respostas incluem `X-Request-ID`. Um identificador externo somente é preservado quando contém caracteres seguros e possui no máximo 64 caracteres; caso contrário, o backend gera um identificador novo. O header é exposto por CORS para diagnóstico controlado.

[Voltar](README.md)
