# Variáveis de ambiente

## Django e rede

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `SECRET_KEY` | Sim | Todos | `configure-no-secret-manager` | Assinaturas internas Django | Sim |
| `DEBUG` | Não | Dev | `True` | Debug do Django | Não |
| `ALLOWED_HOSTS` | Sim em prod | Todos | `api.example.test` | Hosts aceitos | Não |
| `TRUST_PROXY_CLIENT_IP_HEADERS` | Não | Prod | `False` | Confiar em IP enviado pelo proxy | Não |
| `FRONTEND_URL` | Sim em prod | Todos | `https://app.example.test` | Links de redefinição | Não |
| `CORS_ALLOWED_ORIGINS` | Sim em prod | Prod | `https://app.example.test` | Origens permitidas | Não |
| `CSRF_TRUSTED_ORIGINS` | Conforme uso | Prod | `https://app.example.test` | Origens CSRF confiáveis | Não |

## Banco e cache

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `DATABASE_URL` | Sim | Todos | `postgres://usuario:senha@db:5432/elo` | Conexão principal | Sim |
| `POSTGRES_DB` | Docker | Dev | `elo_terapeutico` | Banco do container | Não |
| `POSTGRES_USER` | Docker | Dev | `postgres` | Usuário do container | Não |
| `POSTGRES_PASSWORD` | Docker | Dev | `configure-localmente` | Senha do container | Sim |
| `POSTGRES_HOST` | Não | Dev | `localhost` | Host auxiliar | Não |
| `POSTGRES_PORT` | Não | Dev | `5432` | Porta auxiliar | Não |
| `REDIS_URL` | Sim em prod | Prod | `rediss://cache.example.test:6380/1` | Cache/rate limit | Pode ser |

## JWT e criptografia

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `JWT_SECRET` | Sim | Todos | `configure-outro-segredo` | Assinatura JWT | Sim |
| `JWT_ACCESS_MINUTES` | Não | Todos | `30` | Vida do access token | Não |
| `JWT_REFRESH_DAYS` | Não | Todos | `7` | Vida do refresh token | Não |
| `FIELD_ENCRYPTION_KEY` | Sim | Todos | `configure-chave-de-dados` | Campos criptografados v1 | Sim |
| `FIELD_ENCRYPTION_KEY_V2` | Em rotação | Todos | `configure-nova-chave` | Nova versão de chave | Sim |
| `PASSWORD_RESET_TIMEOUT` | Não | Todos | `900` | Validade do reset em segundos | Não |

## Storage e documentos

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `AZURE_STORAGE_CONNECTION_STRING` | Quando Azure | Prod | `configure-no-secret-manager` | Acesso ao Blob | Sim |
| `AZURE_CONTAINER_NAME` | Quando Azure | Prod | `elo-terapeutico` | Container | Não |
| `AZURE_URL_EXPIRATION_SECS` | Não | Prod | `300` | Expiração de URLs | Não |
| `PRIVATE_MEDIA_STORAGE_REQUIRED` | Recomendado | Prod | `True` | Bloquear filesystem local | Não |
| `DOCUMENT_CLINIC_NAME` | Não | Todos | `Clínica Exemplo` | Cabeçalho de documentos | Não |
| `DOCUMENT_CLINIC_ADDRESS` | Não | Todos | `Endereço institucional` | Documentos | Pode ser |
| `DOCUMENT_CLINIC_PHONE` | Não | Todos | `Telefone institucional` | Documentos | Pode ser |

## Asaas e billing

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `ASAAS_API_KEY` | Sim em prod | Prod | `configure-no-secret-manager` | API Asaas | Sim |
| `ASAAS_BASE_URL` | Sim | Todos | `https://api-sandbox.asaas.com/v3` | Endpoint do gateway | Não |
| `ASAAS_WEBHOOK_TOKEN` | Sim em prod | Prod | `configure-token-distinto` | Autenticar webhook | Sim |
| `BILLING_TRIAL_DAYS` | Não | Todos | `7` | Período de teste | Não |
| `BILLING_DEFAULT_CURRENCY` | Não | Todos | `BRL` | Moeda padrão | Não |
| `BILLING_ENFORCE_PATIENT_LIMITS` | Conforme ambiente | Teste/prod | `True` | Limites do plano | Não |

## E-mail

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `DEFAULT_FROM_EMAIL` | Sim em prod | Todos | `noreply@example.test` | Remetente | Não |
| `EMAIL_HOST` | Sim em prod | Prod | `smtp.example.test` | Servidor SMTP | Não |
| `EMAIL_PORT` | Não | Prod | `587` | Porta SMTP | Não |
| `EMAIL_HOST_USER` | Sim em prod | Prod | `usuario-smtp` | Login SMTP | Sim |
| `EMAIL_HOST_PASSWORD` | Sim em prod | Prod | `configure-no-secret-manager` | Senha SMTP | Sim |

## Frontend

| Variável | Obrigatória | Ambiente | Exemplo seguro | Finalidade | Sensível |
| --- | ---: | --- | --- | --- | ---: |
| `NEXT_PUBLIC_API_URL` | Sim | Frontend | `https://api.example.test/api/v1/` | URL pública da API | Não |

Variáveis com prefixo `NEXT_PUBLIC_` são incorporadas ao bundle e nunca podem conter segredo.

[Voltar](README.md)
