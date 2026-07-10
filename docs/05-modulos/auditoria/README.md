# Módulo de auditoria

**Status: implementado.**

## Finalidade

Registrar ações sensíveis com contexto técnico suficiente para rastreabilidade e sem copiar conteúdo clínico para o log.

## Modelo AuditLog

Campos: usuário, ação, IP, user agent, timestamp, content type, object ID e representação técnica.

Ações: `VIEW`, `CREATE`, `UPDATE`, `DELETE`, `EXPORT`, `ANONYMIZE`.

## Regras

- registros não podem ser atualizados nem deletados pelo model;
- representação padrão é `app.Model#id`, evitando `__str__` potencialmente sensível;
- caracteres de controle são removidos;
- IP de proxy só é aceito quando `TRUST_PROXY_CLIENT_IP_HEADERS=True`;
- Azure client IP e primeiro `X-Forwarded-For` são validados;
- falha ao criar log gera evento de erro sem conteúdo sensível, mas não aborta a operação;
- `AuditLogMixin` cobre retrieve/create/update/destroy quando aplicado.

## Administração

Logs são consultados no backoffice. Não existe API pública própria documentada.

## Segurança

Imutabilidade no model não impede alteração direta por administrador do banco. Produção precisa de privilégios mínimos, backup, retenção, monitoramento e, quando necessário, trilha externa append-only.

## Testes

`apps/audit/tests/test_audit_security.py` valida minimização, IP confiável e normalização. Outros módulos testam eventos específicos.

## Limitações

- cobertura depende de cada view/serviço chamar o mixin ou `log_access`;
- falha de auditoria é fail-open;
- política de retenção não está codificada;
- acesso ao próprio log precisa ser auditado operacionalmente.

[Voltar aos módulos](../README.md)
