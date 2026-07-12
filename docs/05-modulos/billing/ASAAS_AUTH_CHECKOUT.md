# Configuração do Asaas, checkout e autenticação

Este guia descreve a configuração operacional do Asaas e o fluxo de autenticação usado pelo Elo Terapêutico.

## 1. Origem das variáveis de ambiente

### Docker Compose

O Docker Compose usa exclusivamente o arquivo `.env` localizado na raiz do repositório:

```text
EloTerapeutico/
├── docker-compose.yml
├── .env
├── backend/
└── frontend/
```

O arquivo real `.env` não deve ser versionado. Use `.env.example` como referência.

As variáveis críticas são injetadas explicitamente nos serviços `backend` e `worker`:

```text
SECRET_KEY
JWT_SECRET
DATABASE_URL
FIELD_ENCRYPTION_KEY
FRONTEND_URL
CORS_ALLOWED_ORIGINS
ASAAS_API_KEY
ASAAS_BASE_URL
ASAAS_WEBHOOK_TOKEN
```

Após alterar `.env`, recrie os processos que dependem dessas variáveis:

```bash
docker compose up -d --force-recreate backend worker
```

Não é necessário apagar volumes nem o banco de dados.

### Backend executado diretamente

Ao executar `python manage.py runserver` dentro de `backend/`, o arquivo local de referência é `backend/.env`.

O carregamento realizado por `django-environ` não sobrescreve variáveis já presentes no processo. Portanto, uma variável exportada no shell ou injetada pelo Docker tem precedência sobre o arquivo local.

## 2. Ambientes do Asaas

### Sandbox

```text
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
```

### Produção

```text
ASAAS_BASE_URL=https://api.asaas.com/v3
```

Somente esses dois endpoints oficiais são aceitos pelo gateway. Produção rejeita URL de Sandbox durante o startup.

Nunca registre ou exponha:

- `ASAAS_API_KEY`;
- `ASAAS_WEBHOOK_TOKEN`;
- JWT;
- CPF/CNPJ completo em logs;
- número de cartão ou CVV.

## 3. Validação de configuração

O Django registra checagens de segurança para:

- chave da API ausente;
- URL do Asaas ausente ou inválida;
- token de webhook ausente.

Em desenvolvimento, a ausência gera warning e o checkout retorna erro estável `ASAAS_CONFIGURATION_ERROR` com HTTP 503.

Em produção, a configuração incompleta impede uma inicialização considerada válida pelo `check --deploy`.

Execute:

```bash
docker compose exec backend python manage.py check --deploy
```

## 4. CORS do checkout

O frontend envia o header `Idempotency-Key`. O backend mantém os headers padrão do `django-cors-headers` e adiciona explicitamente:

```python
CORS_ALLOW_HEADERS = [
    *default_headers,
    "idempotency-key",
]
```

Em desenvolvimento, a origem padrão permitida é:

```text
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

Produção deve listar apenas os domínios reais. Não use `CORS_ALLOW_ALL_ORIGINS=True` em produção.

Teste manual:

```bash
curl -i -X OPTIONS \
  http://localhost:8000/api/v1/billing/checkout/create/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type,idempotency-key"
```

A resposta deve incluir `Access-Control-Allow-Origin: http://localhost:3000` e `idempotency-key` em `Access-Control-Allow-Headers`.

## 5. Idempotência do checkout

O endpoint aceita a chave no body e no header:

```json
{
  "idempotency_key": "uuid-ou-identificador-estavel"
}
```

```text
Idempotency-Key: uuid-ou-identificador-estavel
```

A precedência é:

1. valor do body;
2. valor do header;
3. compatibilidade legada somente nas rotas antigas.

Novos clientes não devem depender da geração automática de chave.

A chave é armazenada com namespace do usuário. Assim, dois usuários podem usar o mesmo UUID sem colisão, enquanto a combinação `usuário + chave` permanece única.

Uma repetição:

- retorna a contratação já registrada;
- não cria outro cliente no Asaas;
- não cria outra assinatura;
- não cria outra cobrança;
- mantém a mesma resposta de pedido e pagamentos.

Pedidos `FAILED` permitem uma nova tentativa com uma chave nova. Um pedido `PENDING` é reutilizado para a mesma opção comercial. Outra contratação concorrente retorna `CHECKOUT_ALREADY_PENDING` com o identificador público do pedido existente.

## 6. Conversão do trial para plano pago

O trial não bloqueia a contratação paga.

Fluxo:

1. o usuário permanece com assinatura `TRIALING` e acesso válido;
2. o backend cria um `BillingOrder` separado e registra a intenção de conversão;
3. o pedido fica `PENDING` após a criação no Asaas;
4. a assinatura continua `TRIALING` enquanto o pagamento aguarda confirmação;
5. `PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED` ou confirmação equivalente ativa o plano pago;
6. o serviço atualiza plano, pedido, período e identificadores do gateway de forma atômica.

Se o gateway falhar:

- somente o pedido fica `FAILED`;
- o trial preserva sua data original;
- o acesso do trial não é cancelado;
- uma nova tentativa pode ser iniciada com outra chave.

O frontend nunca ativa assinatura.

## 7. Respostas de erro

O contrato de erro é:

```json
{
  "error": {
    "code": "ASAAS_CONFIGURATION_ERROR",
    "message": "A integração de pagamentos não está configurada.",
    "details": {}
  }
}
```

Mapeamento principal:

| Situação | Código | HTTP |
|---|---|---:|
| configuração ausente ou inválida | `ASAAS_CONFIGURATION_ERROR` | 503 |
| credencial rejeitada | `ASAAS_AUTHENTICATION_ERROR` | 502 |
| dados inválidos | `ASAAS_VALIDATION_ERROR` | 400 |
| timeout ou indisponibilidade | `ASAAS_UNAVAILABLE` | 503 |
| pedido já pendente | `CHECKOUT_ALREADY_PENDING` | 409 |
| erro de validação do checkout | `CHECKOUT_VALIDATION_ERROR` | 400 |

Com `DEBUG=True`, uma mensagem segura do Asaas pode ser exibida. Em produção, o detalhe interno é ocultado.

## 8. Normalização de dados

Antes de chamar o gateway, o backend valida ou normaliza:

- nome não vazio;
- e-mail válido;
- CPF com 11 dígitos ou CNPJ com 14 dígitos;
- telefone com DDD, usando apenas números;
- vencimento igual ou posterior à data atual;
- valor maior que zero;
- forma de pagamento reconhecida.

Cartão requer tokenização segura ou checkout hospedado. O Elo Terapêutico não deve receber ou persistir CVV e número completo do cartão.

## 9. Webhook

Endpoint oficial:

```text
POST /api/v1/billing/webhooks/asaas/
```

Em desenvolvimento com túnel:

```text
https://DOMINIO-NGROK/api/v1/billing/webhooks/asaas/
```

O Asaas deve enviar:

```text
asaas-access-token: valor-de-ASAAS_WEBHOOK_TOKEN
```

O webhook:

- não usa JWT;
- exige o token próprio em produção;
- persiste o evento antes do processamento;
- deduplica por ID ou hash;
- responde HTTP 200 após recebimento válido;
- mantém tentativas e backoff persistidos;
- não ativa assinatura a partir de dados enviados pelo frontend.

## 10. Autenticação e entitlement

Autenticação e assinatura são responsabilidades independentes:

- autenticação confirma a identidade;
- entitlement decide quais módulos privados podem ser usados.

Login, refresh, logout, perfil e rotas de regularização de billing permanecem acessíveis sem assinatura ativa.

Após login:

1. a sessão antiga é limpa;
2. access e refresh tokens são armazenados;
3. `/auth/me/` confirma o usuário autenticado;
4. `/billing/entitlement/` decide o destino;
5. `next` só é aceito quando começa com `/` e não começa com `//`.

Destino padrão:

- ativo ou trial válido: rota solicitada ou `/dashboard`;
- sem assinatura: `/planos`;
- pagamento pendente, vencido ou suspenso: `/billing`;
- checkout solicitado: permanece acessível para regularização.

## 11. Cookies e renovação

Cookies usados:

```text
auth_token
auth_refresh_token
auth_role
```

Configuração:

- `path=/`;
- `SameSite=Lax`;
- `Secure=false` em desenvolvimento;
- `Secure=true` em produção.

A renovação do Axios é single-flight: apenas uma chamada de refresh é executada, e requisições concorrentes aguardam a mesma promessa.

O retry:

- ocorre no máximo uma vez;
- não renova a própria rota de refresh;
- atualiza Authorization;
- salva refresh rotacionado;
- preserva body e headers originais;
- preserva `Idempotency-Key` durante retry de checkout.

Refresh inválido limpa todos os cookies e redireciona uma única vez para login.

Os tokens ainda são acessíveis ao JavaScript. A migração para cookies HttpOnly controlados pelo backend permanece uma melhoria de segurança recomendada; enquanto isso, mantenha CSP restritiva e evite scripts de terceiros desnecessários.

## 12. Health check

Rota administrativa:

```text
GET /api/v1/billing/integrations/asaas/health/
```

Exemplo:

```json
{
  "gateway": "ASAAS",
  "connected": true,
  "configured": true,
  "environment": "SANDBOX",
  "error_code": null,
  "last_webhook_at": null,
  "pending_events": 0,
  "failed_events": 0
}
```

A resposta nunca inclui credenciais.

## 13. Validação manual do Sandbox

Suba o ambiente sem apagar volumes:

```bash
docker compose up -d --build --force-recreate
```

Confira a configuração carregada:

```bash
docker compose exec backend python manage.py shell -c "
from django.conf import settings
key = settings.ASAAS_API_KEY
print('Chave carregada:', bool(key))
print('Tamanho:', len(key))
print('URL:', settings.ASAAS_BASE_URL)
"
```

Teste a conectividade:

```bash
docker compose exec backend python manage.py shell -c "
from apps.billing.services.gateways.asaas import AsaasGateway
print(AsaasGateway().health_check())
"
```

Valide:

1. cadastro pelo fluxo pago;
2. login sem loop;
3. checkout com dados válidos do Sandbox;
4. cliente, assinatura ou cobrança no painel Asaas;
5. pedido e pagamentos locais;
6. webhook de confirmação;
7. ativação somente após confirmação;
8. trial contratando plano pago;
9. refresh durante checkout;
10. ausência de cobrança duplicada.

## 14. Testes automatizados

Os testes do backend usam mocks ou gateways falsos e não dependem da internet. Eles cobrem:

- configuração ausente;
- URL inválida;
- autenticação rejeitada;
- timeout;
- normalização de dados;
- CORS e `Idempotency-Key`;
- trial para plano pago;
- falha sem cancelamento do trial;
- idempotência;
- pedido pendente;
- nova tentativa após `FAILED`;
- ativação após pagamento confirmado;
- contrato público de erros 400 e 503.
