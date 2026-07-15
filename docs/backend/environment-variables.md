# Variáveis de ambiente do backend

## Princípios

- use `backend/.env.example` ao executar o backend diretamente;
- use o `.env` da raiz ao executar com Docker Compose;
- nunca versione credenciais reais;
- mantenha segredos diferentes para Django, JWT, criptografia e webhooks;
- valores de exemplo devem ser evidentemente fictícios;
- produção deve falhar de forma segura quando uma configuração obrigatória estiver ausente.

## Django e HTTP

| Variável | Obrigatória | Padrão local | Finalidade |
| --- | --- | --- | --- |
| `SECRET_KEY` | Sim | valor fictício no example | Assinatura criptográfica do Django |
| `DEBUG` | Sim por ambiente | `True` local | Habilita recursos de desenvolvimento |
| `ALLOWED_HOSTS` | Sim | hosts locais | Hosts aceitos pelo Django |
| `FRONTEND_URL` | Sim | `http://localhost:3000` | URL usada em links e redirecionamentos |
| `CORS_ALLOWED_ORIGINS` | Sim | frontend local | Origens autorizadas no CORS |
| `TRUST_PROXY_CLIENT_IP_HEADERS` | Não | `False` | Confia em headers de IP somente atrás de proxy controlado |

Em produção, `DEBUG` deve ser falso e `ALLOWED_HOSTS`/CORS devem conter apenas domínios conhecidos.

## SQL Explorer administrativo

| Variável | Obrigatória | Padrão local | Finalidade |
| --- | --- | --- | --- |
| `ADMIN_SQL_EXPLORER_ENABLED` | Não | `False` | Registra a ferramenta somente em ambiente não produtivo autorizado |
| `ADMIN_SQL_EXPLORER_DATABASE_ALIAS` | Não | `default` | Alias de banco usado pela inspeção; prefira usuário read-only |
| `ADMIN_SQL_EXPLORER_MAX_ROWS` | Não | `100` | Limite de registros retornados, limitado internamente a 500 |
| `ADMIN_SQL_EXPLORER_TIMEOUT_MS` | Não | `2000` | Timeout da instrução, limitado internamente a 10 segundos |
| `ADMIN_SQL_EXPLORER_ALLOWED_TABLES` | Quando habilitado | vazio | Allowlist de tabelas separadas por vírgula |

A ferramenta é desabilitada por padrão. Nos settings de produção, `ADMIN_SQL_EXPLORER_ENABLED=True` interrompe a inicialização da aplicação. Além da flag, o usuário precisa ser superusuário e possuir atribuição explícita da permissão `core.use_sql_explorer`. Consulte [SQL Explorer administrativo](../08-seguranca/sql-explorer.md).

## Banco de dados

| Variável | Obrigatória | Padrão local | Finalidade |
| --- | --- | --- | --- |
| `DATABASE_URL` | Sim | SQLite local | Conexão principal do Django |
| `POSTGRES_DB` | Docker | `config` | Nome do banco PostgreSQL |
| `POSTGRES_USER` | Docker | `postgres` | Usuário do PostgreSQL |
| `POSTGRES_PASSWORD` | Docker | sem padrão seguro | Senha do PostgreSQL |
| `POSTGRES_HOST` | Fora do Docker | `localhost` | Host do PostgreSQL |
| `POSTGRES_PORT` | Fora do Docker | `5432` | Porta do PostgreSQL |

Exemplo local sem credencial real:

```env
DATABASE_URL=sqlite:///local.sqlite3
```

Exemplo estrutural para PostgreSQL:

```env
DATABASE_URL=postgres://usuario:senha@host:5432/banco
```

Não copie o segundo exemplo literalmente para produção.

## JWT e recuperação de senha

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `JWT_SECRET` | Sim | sem padrão seguro | Assinatura dos tokens JWT |
| `JWT_ACCESS_MINUTES` | Não | `30` | Duração do access token |
| `JWT_REFRESH_DAYS` | Não | `7` | Duração do refresh token |
| `PASSWORD_RESET_TIMEOUT` | Não | `900` | Validade do token de redefinição, em segundos |

`JWT_SECRET` não deve reutilizar `SECRET_KEY`.

## Criptografia de campos

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `FIELD_ENCRYPTION_KEY` | Sim em produção | chave local de desenvolvimento | Criptografa campos textuais sensíveis |
| `FIELD_ENCRYPTION_KEY_V2` | Somente em rotação | vazio | Nova chave durante migração/rotação |

A chave de desenvolvimento não é adequada para dados reais. Faça backup seguro das chaves; sem elas, dados criptografados podem ficar irrecuperáveis.

## Documentos

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `DOCUMENT_CLINIC_NAME` | Não | `Elo Terapêutico` | Nome exibido em documentos |
| `DOCUMENT_CLINIC_ADDRESS` | Não | vazio | Endereço institucional |
| `DOCUMENT_CLINIC_PHONE` | Não | vazio | Telefone institucional |

Evite colocar dados pessoais de pacientes nessas variáveis.

## Azure Blob Storage

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `AZURE_STORAGE_CONNECTION_STRING` | Quando Azure estiver ativo | vazio | Conexão com a conta de storage |
| `AZURE_CONTAINER_NAME` | Não | `elo-terapeutico` | Container usado pela aplicação |
| `AZURE_URL_EXPIRATION_SECS` | Não | `300` | Validade de URLs temporárias |
| `PRIVATE_MEDIA_STORAGE_REQUIRED` | Produção clínica | `False` local | Exige backend de mídia privada |

A connection string é segredo. O container deve ser privado.

## Billing e Asaas

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `BILLING_ENABLED` | Não | `True` | Habilita regras de billing |
| `ASAAS_API_KEY` | Para chamadas reais | vazio | Autenticação na API Asaas |
| `ASAAS_BASE_URL` | Sim quando billing ativo | sandbox | URL base do gateway |
| `ASAAS_WEBHOOK_TOKEN` | Para webhooks | valor local fictício | Validação do webhook |
| `BILLING_TRIAL_DAYS` | Não | `7` | Duração do teste gratuito |
| `BILLING_DEFAULT_CURRENCY` | Não | `BRL` | Moeda padrão |
| `BILLING_GRACE_PERIOD_DAYS` | Não | `5` | Período de carência |
| `BILLING_MAX_INSTALLMENTS` | Não | `12` | Limite de parcelas |
| `BILLING_WEBHOOK_MAX_RETRIES` | Não | `5` | Limite de reprocessamentos |
| `BILLING_WEBHOOK_PROCESS_INLINE` | Não | `True` local | Processa webhook inline em dev/testes |
| `BILLING_RECONCILIATION_ENABLED` | Não | `True` | Habilita reconciliação |
| `BILLING_RECONCILIATION_INTERVAL_MINUTES` | Não | `60` | Intervalo de reconciliação |
| `BILLING_CHECKOUT_EXPIRATION_MINUTES` | Não | `30` | Expiração do checkout |

Produção deve usar credenciais de produção, webhook autenticado e processamento persistido.

## E-mail

| Variável | Obrigatória | Padrão local | Finalidade |
| --- | --- | --- | --- |
| `EMAIL_BACKEND` | Não | backend de console | Implementação de envio |
| `DEFAULT_FROM_EMAIL` | Sim em produção | endereço fictício | Remetente padrão |
| `EMAIL_HOST` | SMTP | host fictício | Servidor SMTP |
| `EMAIL_PORT` | SMTP | `587` | Porta SMTP |
| `EMAIL_HOST_USER` | SMTP | vazio | Usuário SMTP |
| `EMAIL_HOST_PASSWORD` | SMTP | vazio | Senha SMTP |
| `EMAIL_USE_TLS` | Não | `True` | Ativa TLS |
| `EMAIL_TIMEOUT` | Não | `15` | Timeout de envio em segundos |

## Comunicações

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `COMMUNICATIONS_ENABLED` | Não | `True` | Habilita o módulo |
| `COMMUNICATIONS_BATCH_SIZE` | Não | `50` | Tamanho do lote do worker |
| `COMMUNICATIONS_MAX_ATTEMPTS` | Não | `5` | Máximo de tentativas |
| `COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES` | Não | `15` | Detecta itens abandonados |
| `COMMUNICATIONS_DEFAULT_TIMEZONE` | Não | `America/Sao_Paulo` | Fuso das automações |
| `COMMUNICATIONS_REPLY_TO` | Não | vazio | Endereço de resposta |

## WhatsApp Business

| Variável | Obrigatória | Finalidade |
| --- | --- | --- |
| `WHATSAPP_PROVIDER` | Quando o canal estiver ativo | Seleciona o adapter |
| `WHATSAPP_API_BASE_URL` | Provider dependente | URL da API |
| `WHATSAPP_ACCESS_TOKEN` | Sim para envio | Token de acesso |
| `WHATSAPP_PHONE_NUMBER_ID` | Sim para envio | Identificador do número |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Para webhook | Verificação inicial |
| `WHATSAPP_APP_SECRET` | Para assinatura | Valida payload recebido |

Com configuração incompleta, o canal deve permanecer desativado.

## SMS

| Variável | Obrigatória | Finalidade |
| --- | --- | --- |
| `SMS_PROVIDER` | Quando ativo | Seleciona o adapter |
| `SMS_API_KEY` | Quando ativo | Autenticação no provider |
| `SMS_SENDER` | Quando ativo | Remetente configurado |

## Frontend

`NEXT_PUBLIC_API_URL` é referência do frontend e aparece no example do backend por conveniência:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/
```

Variáveis iniciadas com `NEXT_PUBLIC_` são expostas ao navegador e nunca devem conter segredo.

## Checklist de produção

- [ ] `DEBUG=False`;
- [ ] `ADMIN_SQL_EXPLORER_ENABLED=False`;
- [ ] segredos longos, aleatórios e independentes;
- [ ] PostgreSQL gerenciado e backup testado;
- [ ] CORS e hosts restritos;
- [ ] storage privado configurado;
- [ ] SMTP real e remetente verificado;
- [ ] Asaas em ambiente correto;
- [ ] webhook autenticado;
- [ ] workers ativos e monitorados;
- [ ] rotação e recuperação de segredos documentadas;
- [ ] nenhum `.env` ou segredo presente no Git.
