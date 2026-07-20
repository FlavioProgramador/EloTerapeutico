# Módulo de auditoria

**Status: implementado e organizado por camadas.**

## Finalidade

Registrar evidências mínimas de operações sensíveis com contexto suficiente para rastreabilidade, sem copiar conteúdo clínico, credenciais ou payloads completos. Auditoria não substitui logging técnico, métricas, tracing ou SIEM.

## Compatibilidade histórica

- package Python: `apps.audit`;
- app label: `audit`;
- model: `AuditLog`;
- tabela física: `users_auditlog`;
- migration inicial baseada em `SeparateDatabaseAndState`.

A reorganização do package não renomeia a tabela nem reescreve migrations históricas.

## Organização

- `models/`: model append-only, QuerySet e manager imutáveis;
- `services/`: escrita canônica, sanitização e contexto HTTP;
- `selectors/`: consultas autorizadas e com `select_related`;
- `integrations/`: adapters para DRF e Django Admin;
- `admin/`: painel somente leitura;
- `types/` e `exceptions/`: contratos tipados;
- `tests/`: integridade, permissões, minimização e arquitetura.

## Escrita

O contrato público é:

```python
from apps.audit.services import record_audit_event
```

`log_access` permanece como adapter compatível. Chamadas diretas a `AuditLog.objects.create()` fora dos services são proibidas.

Mutações executadas dentro de transações usam `transaction.on_commit`. Leituras são gravadas imediatamente. A política padrão permanece fail-open para preservar disponibilidade, enquanto operações que exijam fail-closed devem fornecer uma política explícita.

## Imutabilidade

O model bloqueia `save()` posterior e `delete()`. O QuerySet bloqueia `update()`, `delete()`, `bulk_update()` e `update_or_create()`. A proteção não substitui privilégios mínimos no banco, backups, retenção e eventual trilha externa append-only.

## Minimização

- representação padrão: `app.Model#id`;
- `__str__` do recurso não é usado como fallback;
- User-Agent é normalizado e truncado;
- IP de proxy só é aceito quando `AUDIT_TRUSTED_PROXY_HOPS` ou a configuração legada de proxy confiável estiver habilitada;
- senhas, tokens, cookies, CPF, documentos e conteúdo clínico são removidos de metadata;
- request body completo e headers sensíveis não são persistidos.

O schema histórico ainda não persiste metadata, reason, source ou request ID. Esses valores são validados para política e observabilidade; persistência exige migration aditiva futura.

## Administração e permissões

Não existe API pública própria. O Django Admin é estritamente read-only e só permite visualização para superusers ou usuários com `audit.view_auditlog`. Acesso ao próprio painel gera evento de visualização.

## Retenção

Não existe expurgo HTTP nem comando automático. Retenção, legal hold, backup e eventual purga precisam de decisão jurídica e operacional antes de implementação.

## Testes

`apps/audit/tests/` cobre:

- tabela e app label históricos;
- imutabilidade por instance e QuerySet;
- minimização e proxy confiável;
- política fail-open/fail-closed;
- `transaction.on_commit`;
- integração DRF sem duplicação;
- permissões e Admin read-only;
- guarda arquitetural.

## Limitações

- `object_id` é numérico; recursos UUID exigem evolução própria;
- não há trigger de banco nesta etapa;
- cobertura depende de instrumentação explícita;
- retenção ainda não está codificada.

[Voltar aos módulos](../README.md)
