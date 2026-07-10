# Casos de uso — Billing e administração

# UC-BIL-001 — Contratar assinatura

## Objetivo
Criar cobrança/assinatura no Asaas sem ativação indevida pelo cliente.

## Atores
Usuário autenticado e Asaas.

## Pré-condições
Plano ativo; API key configurada; dados de checkout válidos.

## Fluxo principal
1. Usuário consulta planos.
2. Preview valida plano, ciclo, valor, vencimento e meio.
3. Backend cria cliente Asaas quando necessário.
4. Cria assinatura ou cobrança.
5. Registro local permanece `PENDING`.
6. Asaas envia webhook autenticado.
7. Handler deduplica evento e atualiza assinatura/pagamento.
8. Somente então o plano pode ficar `ACTIVE`.

## Fluxos alternativos
Cobrança única retorna apenas ID, status e URLs públicas necessárias.

## Exceções
Gateway indisponível retorna 502 controlado; cartão sem token seguro é recusado.

## Eventos de auditoria
WebhookEvent registra processamento; logs não devem conter credenciais/payload sensível.

## Regras de segurança
Token de webhook forte, comparação em tempo constante, idempotência e redaction.

## Endpoints relacionados
`/api/v1/billing/*`.

## Status de implementação
Implementado; requer configuração operacional.

---

# UC-BIL-002 — Alterar ou cancelar plano

Usuário autenticado solicita mudança/cancelamento da própria assinatura. Backend coordena gateway, persiste novo estado e retorna dados serializados. Falhas externas não devem marcar sucesso local.

## Status de implementação
Implementado.

---

# UC-ADM-001 — Administrar dados pelo backoffice

## Atores
Staff com permissões específicas.

## Fluxo principal
1. Staff autentica no Django Admin.
2. Menu apresenta somente áreas autorizadas.
3. Operação passa por ModelAdmin, regras e banco.
4. Dados confidenciais mantêm restrições específicas.

## Exceções
Sem `is_staff` ou permissão, acesso é recusado.

## Regras de segurança
Menor privilégio, revisão de staff, proteção do SQL Explorer e auditoria.

## Status de implementação
Implementado.

[Voltar](README.md)
