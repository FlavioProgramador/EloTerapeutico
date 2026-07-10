# Módulo de assinaturas, pagamentos e integrações

**Status:** refatorado para mensal recorrente, anual à vista e anual parcelado. Requer Asaas e webhook configurados.

## Finalidade

Controlar a contratação do Elo Terapêutico, o direito de acesso do terapeuta, cobranças, parcelas, faturas, inadimplência e integração com o gateway. Este domínio é separado do financeiro clínico de pacientes.

## Arquitetura de domínio

### `Plan`

Define o produto, limites e recursos habilitados. Os campos legados de preço e ciclo permanecem temporariamente para migração.

### `PlanPrice`

Define uma opção comercial do plano:

- `RECURRING`: cobrança recorrente mensal ou anual;
- `ONE_TIME`: pagamento anual à vista;
- `INSTALLMENT`: contratação anual parcelada;
- valor, moeda, desconto, vigência e limite de parcelas.

O backend sempre usa o preço cadastrado. Valores enviados pelo navegador não determinam a cobrança.

### `BillingOrder`

Representa a contratação. Armazena snapshot comercial, valor total, modalidade, quantidade de parcelas, referência externa, IDs do gateway e chave de idempotência.

Status principais: `DRAFT`, `PENDING`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELED`, `REFUNDED`, `CHARGEBACK`, `FAILED` e `EXPIRED`.

### `Subscription`

Representa somente o direito de acesso ao SaaS. Mantém período, carência, cancelamento agendado, suspensão e vínculo com a contratação vigente.

Status: `TRIALING`, `PENDING`, `ACTIVE`, `PAST_DUE`, `SUSPENDED`, `CANCELED` e `EXPIRED`.

### `Payment`

Cada registro representa uma cobrança ou parcela individual. Inclui:

- `installment_number` e `installment_count`;
- valor bruto e líquido;
- vencimento original e atual;
- status financeiro;
- forma de pagamento;
- links de fatura, boleto e comprovante;
- IDs de assinatura e parcelamento do Asaas;
- payload sanitizado.

### `WebhookEvent`

Fila persistida de eventos do gateway. Registra estado, tentativas, próxima tentativa, erro controlado e payload sanitizado.

## Fluxos comerciais

### Mensal recorrente

1. Cria contratação local com idempotência.
2. Cria assinatura mensal no Asaas.
3. Mantém acesso pendente.
4. Webhook confirmado ativa um mês de calendário.
5. Inadimplência aplica carência e pode suspender o acesso.

### Anual à vista

1. Cria cobrança única.
2. Persiste a fatura local.
3. Confirmação concede doze meses de calendário.
4. A renovação é uma nova contratação.

### Anual parcelado

1. O usuário escolhe entre o mínimo e o máximo configurados.
2. O backend envia `installmentCount` e `totalValue` ao Asaas.
3. Salva o ID do parcelamento.
4. Sincroniza todas as cobranças do parcelamento.
5. Cada parcela aparece como “Parcela X de Y”.
6. A confirmação válida concede o período anual conforme a política de acesso.

## Idempotência

`checkout/create/` exige uma chave de idempotência para o contrato novo. Repetições com a mesma chave retornam a mesma contratação e não geram outra cobrança.

O endpoint legado que envia apenas `plan_id` ou `plan_slug` permanece temporariamente compatível e gera uma chave interna, mas novos clientes devem sempre enviar `Idempotency-Key`.

## Troca de plano

A contratação nova é criada sem substituir a assinatura vigente. Somente após pagamento confirmado o serviço de acesso:

- troca plano e preço vigentes;
- inicia o novo período;
- atualiza os IDs do gateway;
- marca a assinatura recorrente anterior para cancelamento na reconciliação.

Assim, uma falha no novo checkout não interrompe o plano atual.

## Cancelamento

- **Ao fim do período:** mantém acesso até `access_ends_at`; a reconciliação cancela a recorrência no gateway e encerra a assinatura local.
- **Imediato:** operação explícita separada; não implica estorno automático.
- **Retomar renovação:** remove o cancelamento agendado antes do fim do período.

## Inadimplência

Fluxo padrão:

```text
Pagamento vencido
→ PAST_DUE
→ carência configurável
→ SUSPENDED
→ pagamento confirmado
→ ACTIVE
```

Dados do usuário não são apagados. Acesso a faturas e regularização deve permanecer disponível.

## Webhooks

Eventos são:

1. autenticados;
2. persistidos com redaction;
3. deduplicados por ID/hash;
4. processados com máquina de estados;
5. mantidos para retry quando a contratação ainda não existe;
6. reprocessáveis por worker.

Eventos desconhecidos são registrados como `IGNORED` e não causam erro 500.

### Worker

```bash
python manage.py run_billing_webhook_worker
python manage.py run_billing_webhook_worker --once
```

O worker usa `select_for_update(skip_locked=True)`, lease temporário e retry com backoff.

## Reconciliação

```bash
python manage.py reconcile_billing
python manage.py reconcile_billing --order <uuid-publico>
```

A reconciliação:

- importa parcelas ausentes;
- atualiza cobranças recorrentes;
- suspende assinaturas após carência;
- efetiva cancelamentos ao final do período;
- encerra recorrências anteriores após troca de plano.

## Frontend

O frontend oferece:

- seletor mensal/anual;
- anual à vista ou parcelado;
- cálculo estimado das parcelas;
- checkout com revisão;
- resumo da assinatura;
- cancelamento agendado e retomada;
- resumo financeiro das faturas;
- filtros por status;
- “Parcela X de Y”;
- atualização manual de uma fatura;
- links de cobrança, boleto e comprovante.

## Segurança

- chave do Asaas somente no backend;
- token do webhook comparado de forma segura;
- nenhum dado clínico é enviado ao gateway;
- preço e status nunca são confiados ao frontend;
- payload de auditoria é sanitizado;
- cartão bruto e CVV não são persistidos;
- faturas são filtradas por proprietário;
- transações e locks protegem concorrência;
- respostas públicas não expõem customer ID, token ou payload privado.

## Variáveis

```text
ASAAS_API_KEY
ASAAS_BASE_URL
ASAAS_WEBHOOK_TOKEN
BILLING_TRIAL_DAYS
BILLING_GRACE_PERIOD_DAYS
BILLING_MAX_INSTALLMENTS
BILLING_WEBHOOK_MAX_RETRIES
BILLING_RECONCILIATION_ENABLED
BILLING_RECONCILIATION_INTERVAL_MINUTES
BILLING_CHECKOUT_EXPIRATION_MINUTES
```

## Limitações e riscos residuais

- cartão de crédito permanece desabilitado no frontend até integração com checkout hospedado ou tokenização oficial do Asaas;
- a reconciliação precisa ser agendada no ambiente de produção;
- estorno automático não é aplicado sem política comercial explícita;
- pró-rata não é calculado automaticamente;
- mudanças futuras devem remover os campos legados de preço do `Plan` após a migração completa.

[Voltar aos módulos](../README.md)
