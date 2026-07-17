# Communications app

O app `communications` concentra comunicações operacionais, notificações internas, templates, automações, preferências, configurações de canais, entregas e webhooks.

## Estrutura interna

```text
communications/
├── api/
│   ├── v1/
│   │   ├── serializers/
│   │   ├── permissions/
│   │   └── urls.py
│   └── public/
│       └── urls.py
├── admin/
├── integrations/
│   └── providers/
├── infrastructure/
├── models/
├── selectors/
├── services/
├── signals/
├── tasks/
├── validators/
├── management/commands/
├── migrations/
├── tests/
├── migration_operations.py
├── urls.py
└── urls_public.py
```

Os arquivos `serializers.py`, `channel_serializers.py`, `permissions.py` e `providers.py` permanecem temporariamente como fachadas de compatibilidade. A implementação canônica está nos pacotes internos.

`migration_operations.py` permanece na raiz porque migrations históricas dependem desse caminho.

## Fluxo principal de envio

```text
API ou evento
    ↓
service de criação/agendamento
    ↓
task Celery
    ↓
service de despacho
    ↓
registry de providers
    ↓
e-mail, WhatsApp, SMS ou notificação interna
```

As tasks preservam os nomes Celery públicos existentes. Regras de envio, retry, preferências e transições de status continuam nos services; tasks apenas coordenam a execução assíncrona.

## Providers

As integrações estão em `integrations/providers`:

- `base.py`: contrato, resultado e exceções;
- `registry.py`: resolução de provider por canal e configuração;
- `in_app.py`: notificações dentro do sistema;
- `email.py`: backend Django e SMTP;
- `whatsapp.py`: WhatsApp manual e Meta Cloud;
- `sms.py`: Twilio SMS.

Falhas externas são convertidas em exceções próprias, distinguindo erros permanentes e transitórios.

## API

- `api/v1`: endpoints autenticados, serializers e permissões;
- `api/public`: ações públicas baseadas em token;
- `urls.py` e `urls_public.py`: fachadas que preservam os caminhos incluídos pelo projeto.

Os nomes das rotas, basenames dos routers e contratos consumidos pelo frontend são preservados.

## Signals

Os signals são separados pela origem do evento:

- `agenda.py`;
- `forms.py`;
- `documents.py`;
- `finance.py`;
- `users.py`.

O registro ocorre em `CommunicationsConfig.ready()` por meio do pacote `signals`.

## Tasks

As tasks são organizadas em:

- `dispatch.py`;
- `automations.py`;
- `notifications.py`;
- `maintenance.py`.

O `tasks/__init__.py` importa os módulos para manter o autodiscovery do Celery.

## Documentação complementar

A documentação operacional e arquitetural está em:

```text
docs/05-modulos/comunicacoes/README.md
docs/05-modulos/comunicacoes/configuracao-de-canais.md
docs/05-modulos/comunicacoes/diagnostico-runtime.md
docs/backend/app-architecture.md
```

## Comandos principais

```bash
python manage.py process_communications --sleep 5
python manage.py schedule_communication_automations
python manage.py retry_failed_communications
python manage.py cleanup_expired_communication_tokens
```

## Validação

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest backend/apps/communications backend/apps/core/tests/project/test_api_architecture.py
python backend/apps/core/quality/check_backend_architecture.py
ruff check backend/apps/communications backend/apps/core
```
