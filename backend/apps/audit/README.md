# Audit

## Responsabilidade

`apps.audit` registra evidências mínimas de operações sensíveis. Auditoria não substitui logs técnicos, métricas, tracing ou SIEM e não implementa regras dos domínios consumidores.

## Compatibilidade histórica

- package: `apps.audit`;
- app label: `audit`;
- model: `AuditLog`;
- tabela física preservada: `users_auditlog`;
- migration inicial usa `SeparateDatabaseAndState` e não deve ser reescrita.

## Estrutura

- `models/`: registro append-only e QuerySet imutável;
- `services/`: escrita, sanitização e contexto HTTP;
- `selectors/`: consultas autorizadas e otimizadas;
- `integrations/`: adapters para DRF e Django Admin;
- `admin/`: painel estritamente read-only;
- `types/` e `exceptions/`: contratos públicos;
- `tests/`: integridade, segurança, permissões e arquitetura.

## Escrita

Use somente:

```python
from apps.audit.services import record_audit_event
```

`log_access` permanece como adapter público compatível. Escritas diretas com `AuditLog.objects.create()` fora dos services são proibidas.

Mutações utilizam `transaction.on_commit` quando estão em bloco transacional. Leituras são registradas imediatamente. A política padrão é fail-open para preservar os contratos atuais; operações que exigirem fail-closed devem fornecer `AuditWritePolicy` explícita.

## Minimização

O padrão de representação é `app.Model#id`. User-Agent é normalizado e truncado. Cabeçalhos de proxy só são aceitos quando `AUDIT_TRUSTED_PROXY_HOPS` ou a configuração legada de proxy confiável estiver habilitada. Senhas, tokens, cookies, CPF, conteúdo clínico e payloads completos não devem ser armazenados.

O schema histórico ainda não possui colunas para metadata, reason, source ou request ID. Esses dados são validados para uso seguro na política e observabilidade, mas sua persistência exige migration aditiva futura.

## Imutabilidade e retenção

O model e o QuerySet bloqueiam `save` posterior, `delete`, `update`, `bulk_update` e `update_or_create`. Não existe expurgo HTTP nem comando automático. Retenção, legal hold, backup e eventual expurgo precisam de política aprovada antes de qualquer implementação.

## Permissões

A trilha global só é visível para superusers ou usuários com `audit.view_auditlog`. O Admin não permite criar, alterar, excluir ou exportar registros.

## Validação

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations audit
python manage.py showmigrations users
python apps/core/quality/check_backend_architecture.py
pytest apps/audit -v
```

## Limitações conhecidas

- `object_id` é numérico; recursos UUID exigem evolução própria;
- imutabilidade no banco não usa trigger nesta etapa;
- a cobertura de eventos depende da instrumentação explícita de cada operação;
- retenção ainda precisa de decisão jurídica e operacional.
