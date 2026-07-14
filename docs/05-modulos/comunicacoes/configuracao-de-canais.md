# Configuração de canais de comunicação

Esta documentação descreve o fluxo implementado para configurar, validar, testar, ativar e remover canais no módulo de Comunicações.

## Princípios de segurança

- as configurações são sempre isoladas pelo usuário autenticado;
- segredos são persistidos em `CommunicationChannelConfig.credentials` com `EncryptedTextField`;
- a API nunca retorna senha, token, segredo de aplicativo ou Auth Token;
- o frontend recebe apenas `credential_state`, indicando se cada segredo já foi configurado;
- um campo secreto vazio durante a edição preserva o valor armazenado;
- trocar o provedor de um canal ativo exige confirmação explícita e desativa o canal;
- erros persistidos e exibidos são sanitizados e não incluem payloads externos nem credenciais;
- `FIELD_ENCRYPTION_KEY` é obrigatória e deve ser diferente de `SECRET_KEY` e `JWT_SECRET`.

## Estados

| Estado | Significado |
|---|---|
| `not_configured` | nenhum provedor foi escolhido |
| `incomplete` | existe um rascunho ou faltam campos obrigatórios |
| `validating` | teste de conexão em andamento |
| `configured` | configuração validada e pronta para ativação |
| `error` | credencial, conexão ou configuração rejeitada |
| `unavailable` | indisponibilidade temporária do provedor |

A ativação operacional é representada separadamente por `is_active`. Um canal pode estar configurado e inativo.

## Endpoints

Prefixo: `/api/v1/communications/channels/`

| Método | Rota | Finalidade |
|---|---|---|
| `GET` | `/` | listar canais e schemas seguros de configuração |
| `GET` | `catalog/` | catálogo de provedores e campos suportados |
| `GET` | `{channel}/` | consultar um canal |
| `PATCH` | `{channel}/` | salvar ou editar a configuração |
| `POST` | `{channel}/test-connection/` | validar credenciais e conectividade |
| `POST` | `{channel}/test/` | enviar mensagem de teste controlada |
| `POST` | `{channel}/activate/` | ativar após validação bem-sucedida |
| `POST` | `{channel}/deactivate/` | desativar sem apagar a configuração |
| `POST` | `{channel}/remove/` | apagar credenciais e configuração externa |

Exemplo de configuração SMTP:

```json
{
  "provider": "smtp",
  "metadata": {
    "host": "smtp.example.com",
    "port": 587,
    "use_tls": true,
    "use_ssl": false,
    "timeout": 15,
    "sender_name": "Clínica Exemplo",
    "sender_email": "contato@example.com",
    "reply_to": "respostas@example.com"
  },
  "secrets": {
    "username": "usuario-smtp",
    "password": "senha-de-aplicativo"
  },
  "save_as_draft": false
}
```

## Provedores

### Comunicação interna

Provider: `in_app`.

Não exige credenciais. O teste cria uma notificação real para o usuário autenticado.

### E-mail pelo Django

Provider: `django_email`.

Usa o backend configurado no servidor:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=noreply@example.com
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
EMAIL_TIMEOUT=15
```

Os valores por usuário, como nome do remetente e reply-to, podem ser sobrescritos pela configuração do canal sem expor os segredos globais.

### SMTP personalizado

Provider: `smtp`.

Campos obrigatórios:

- host;
- porta;
- usuário;
- senha;
- nome do remetente;
- e-mail do remetente.

TLS e SSL não podem ser ativados simultaneamente. A validação abre uma conexão autenticada e a fecha sem manter transações de banco abertas.

### WhatsApp manual

Provider: `whatsapp_manual`.

Gera link `wa.me`. O teste apenas prepara o link; não afirma que houve envio, entrega ou leitura. A confirmação continua humana e auditável.

### WhatsApp Business oficial

Provider: `meta_cloud`.

Campos principais:

- `phone_number_id`;
- número comercial;
- token de acesso;
- token de verificação do webhook;
- segredo do aplicativo, quando utilizado;
- versão da Graph API.

A validação consulta a Graph API oficial. O envio usa o endpoint oficial de mensagens. Mensagens rejeitadas por janela, template ou destinatário são registradas como falha sanitizada. Templates oficiais e webhooks continuam sujeitos às regras e aprovações da Meta.

### SMS

Provider: `twilio`.

Campos principais:

- Account SID;
- Auth Token;
- número remetente;
- código de país padrão;
- callback de status, quando configurado.

A validação consulta a conta Twilio. O envio registra o SID externo e, quando a API informar, status e preço sem armazenar o payload bruto.

## Fluxo da interface

O drawer de configuração possui seis etapas:

1. seleção do provedor;
2. credenciais e identificação técnica;
3. remetente;
4. preferências;
5. teste da conexão e mensagem de teste;
6. ativação.

É possível salvar como rascunho em qualquer etapa. O botão **Configurar** nunca fica desabilitado por falta de provedor.

## Processamento assíncrono

Comunicações reais continuam sendo persistidas e processadas pelo worker. Durante o dispatch, o provider é resolvido pela configuração do proprietário e do canal. A fila mantém retentativas, idempotência e histórico de `CommunicationAttempt`.

Testes de canal são operações controladas e limitadas por rate limit; eles não substituem o histórico de comunicações destinado aos pacientes.

## Testes

```bash
cd backend
pytest apps/communications/tests/test_channel_configuration.py -q
pytest apps/communications/tests -q
python manage.py check
python manage.py makemigrations --check --dry-run

cd ../frontend
node --experimental-strip-types --test communications.test.mjs
npm run typecheck
npm run lint
```

As suítes automatizadas não chamam Meta, Twilio ou SMTP externo. Providers externos devem ser mockados nos testes.

## Troubleshooting

### O canal não ativa

Confirme que o estado é `configured`. Salvar os dados não substitui o teste de conexão.

### A senha desapareceu ao editar

É esperado. A API retorna somente `credential_state`. Deixe o campo vazio para manter o segredo existente ou informe um novo valor para substituí-lo.

### A troca de provedor foi bloqueada

Quando o canal está ativo, envie `confirm_provider_change=true`. A troca desativa o canal e exige nova validação.

### Credenciais ficaram inacessíveis

Verifique se `FIELD_ENCRYPTION_KEY` é a mesma usada na gravação. Rotação deve usar `FIELD_ENCRYPTION_KEY_V2` conforme a política do projeto.
