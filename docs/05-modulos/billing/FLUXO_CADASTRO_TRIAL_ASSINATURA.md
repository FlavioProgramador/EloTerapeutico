# Fluxo de cadastro, trial, assinatura e acesso

## Visão geral

O Elo Terapêutico separa autenticação de autorização comercial:

1. a conta é criada;
2. o plano selecionado é persistido;
3. uma assinatura local é criada quando aplicável;
4. o teste gratuito ou checkout é iniciado;
5. o backend aguarda o webhook do gateway;
6. o acesso às APIs privadas só é liberado para `ACTIVE` ou `TRIALING` válido;
7. após a liberação, o usuário conclui o onboarding e entra no dashboard.

Usuários sem acesso comercial continuam autenticáveis e podem abrir planos, checkout, cobrança, perfil, suporte, termos, privacidade e logout.

## Estados internos

| Estado | Regra de acesso | Destino principal |
| --- | --- | --- |
| `PENDING` | bloqueado | `/billing/pending` |
| `TRIALING` | liberado até `trial_ends_at` | `/onboarding` ou `/dashboard` |
| `ACTIVE` | liberado durante o período contratado | `/onboarding` ou `/dashboard` |
| `PAST_DUE` | bloqueado | `/billing/past-due` |
| `SUSPENDED` | bloqueado | `/billing/past-due` |
| `CANCELED` | bloqueado após a perda do período válido | `/billing/expired` |
| `EXPIRED` | bloqueado | `/billing/expired` |

O estado local `PENDING` representa o conceito comercial `PENDING_PAYMENT`, preservando compatibilidade com os dados e integrações existentes.

## Cadastro

Endpoint:

```http
POST /api/v1/auth/register/
```

Campos essenciais:

```json
{
  "full_name": "Nome do profissional",
  "email": "profissional@example.com",
  "phone": "21999999999",
  "password": "senha-segura",
  "password_confirm": "senha-segura",
  "terms_accepted": true,
  "privacy_accepted": true,
  "plan": "profissional",
  "plan_price_slug": "profissional-mensal",
  "billing_cycle": "MONTHLY",
  "payment_mode": "RECURRING",
  "access_mode": "TRIAL"
}
```

Plano e modalidade são opcionais. Sem plano, a conta é criada e o próximo destino é `/planos`.

A operação usa `transaction.atomic()`. Usuário, aceites legais, trial ou assinatura pendente não ficam parcialmente persistidos.

## Teste gratuito

- duração oficial: `BILLING_TRIAL_DAYS`, padrão 7;
- início protegido por `select_for_update()`;
- `trial_used_at` no usuário impede reutilização;
- metadados registram plano, preço, início e duração;
- troca de plano ou cancelamento não reinicia o trial;
- expiração preserva todos os dados.

Comando periódico:

```bash
python manage.py expire_trials
```

Recomendação de agenda Celery Beat ou cron:

```cron
*/30 * * * * cd /app/backend && python manage.py expire_trials
```

## Checkout e ativação

O cadastro pago cria primeiro uma assinatura local `PENDING`, sem liberar ferramentas. No checkout:

- a assinatura pendente é vinculada ao `BillingOrder`;
- o valor é resolvido pelo `PlanPrice` do backend;
- a chave de idempotência é isolada por usuário;
- o gateway localiza ou cria o cliente;
- IDs externos são persistidos;
- uma falha não ativa a assinatura;
- apenas webhook confirmado chama a ativação.

O frontend não determina valor, desconto, período, trial ou status.

## Webhook Asaas

Endpoint:

```http
POST /api/v1/billing/webhooks/asaas/
```

Header oficial:

```text
asaas-access-token: <ASAAS_WEBHOOK_TOKEN>
```

Eventos já tratados pelo domínio de billing incluem criação, confirmação, recebimento, atraso, cancelamento, estorno, reembolso, chargeback e restauração, com persistência e deduplicação em `WebhookEvent`.

## Controle de acesso

A autenticação global `SubscriptionJWTAuthentication` consulta o entitlement para APIs privadas. O frontend apenas melhora a experiência; a segurança é aplicada no backend.

Rotas permitidas para regularização:

- `/api/v1/auth/me/`;
- `/api/v1/auth/onboarding/`;
- endpoints de autenticação e recuperação;
- `/api/v1/billing/**`;
- documentação da API.

## Onboarding

Endpoint:

```http
GET|POST|PATCH /api/v1/auth/onboarding/
```

Permite configurar nome profissional, especialidade, registro, clínica, telefone, endereço, duração padrão e horários de atendimento. Campos opcionais podem ser concluídos depois. Toda atualização gera `AuditLog`.

## Variáveis de ambiente

```env
BILLING_REQUIRE_SUBSCRIPTION=True
BILLING_TRIAL_DAYS=7
BILLING_ENFORCE_PATIENT_LIMITS=True
BILLING_CHECKOUT_EXPIRATION_MINUTES=30
ASAAS_API_KEY=
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
ASAAS_WEBHOOK_TOKEN=
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## Comandos

```bash
docker compose up -d --build

docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py check
docker compose exec backend pytest apps/billing/tests -q

cd frontend
npm ci
npm run lint
npm run typecheck
npm run test:auth
npm run build
```

## Compatibilidade e migração

A migração `users.0003_account_lifecycle_and_onboarding` adiciona campos nulos ou com defaults seguros. Usuários existentes continuam válidos. Contas antigas sem assinatura podem entrar e são direcionadas para `/planos`; superusuários e administradores internos mantêm o bypass já existente.

Nenhum paciente, prontuário, documento ou registro financeiro é excluído por cancelamento ou expiração.

## Limitações conhecidas

- os textos legais incluídos são operacionais e precisam de revisão jurídica antes do lançamento;
- notificações de conta/trial usam o backend de e-mail configurado; demais notificações comerciais devem ser conectadas à fila Celery conforme a estratégia de produto;
- testes end-to-end com credencial real e webhook público dependem do Sandbox Asaas configurado externamente;
- o campo existente `started_at`, combinado aos metadados `trial_started_at`, representa o início do trial sem duplicar semântica no banco.
