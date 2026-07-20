# Billing e integrações externas

## Separação de domínios

- `apps.finances`: receitas, despesas, mensalidades e pagamentos de pacientes;
- `apps.billing`: planos, assinatura SaaS, checkout, cobranças e gateway.

Uma alteração em billing não deve criar ou modificar transações clínicas sem um caso de uso explícito.

## Integrações

Gateways externos permanecem em `apps.billing.integrations`. O domínio `finances` não conhece credenciais Asaas, checkout ou webhooks SaaS.

## Segurança

- nunca registrar segredos, tokens ou payloads financeiros integrais;
- validar webhooks antes do processamento;
- usar idempotência em cobranças e reconciliação;
- armazenar arquivos clínicos em storage privado;
- aplicar timeout finito em toda chamada de rede.
