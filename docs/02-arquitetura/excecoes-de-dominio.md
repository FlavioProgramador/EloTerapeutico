# Exceções de domínio

As classes de erro controlado ficam em `backend/apps/core/exceptions.py`. O tratamento HTTP/DRF fica separado em `backend/apps/core/exception_handler.py`.

| Exceção | HTTP | Uso |
|---|---:|---|
| `ApplicationError` | 400 | Erro controlado genérico ou validação na fronteira da aplicação |
| `AuthorizationError` | 403 | Ator autenticado sem acesso ao recurso |
| `ObjectNotFoundError` | 404 | Recurso inexistente ou não visível ao tenant |
| `DomainIntegrityError` | 409 | Conflito de estado, concorrência ou integridade |
| `BusinessRuleViolation` | 422 | Dados válidos, mas regra de negócio impede a ação |
| `ApplicationOperationError` | 500 | Falha controlada sem exposição de detalhes internos |

## Regras

- serializers continuam usando `serializers.ValidationError` para formato e validação de entrada;
- models e validators Django continuam usando `django.core.exceptions.ValidationError`;
- services usam a hierarquia de aplicação para autorização, inexistência, conflito e regras de negócio;
- views não devem capturar essas exceções para montar respostas manualmente;
- erros técnicos de gateway, transporte e provider permanecem próximos aos adapters e são traduzidos na fronteira apropriada;
- mensagens devem ser seguras para exposição e nunca incluir SQL, tokens, CPF ou conteúdo clínico.
