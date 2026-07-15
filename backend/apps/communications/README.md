# Communications app

A documentação operacional e arquitetural deste app está em:

```text
docs/05-modulos/comunicacoes/README.md
```

O fluxo de configuração, validação, teste e ativação dos canais está documentado em:

```text
docs/05-modulos/comunicacoes/configuracao-de-canais.md
```

Para erros de runtime, banco sem migrations ou respostas `COMMUNICATIONS_DATABASE_NOT_READY`, consulte:

```text
docs/05-modulos/comunicacoes/diagnostico-runtime.md
```

Comandos principais:

```bash
python manage.py process_communications --sleep 5
python manage.py schedule_communication_automations
python manage.py retry_failed_communications
python manage.py cleanup_expired_communication_tokens
```
