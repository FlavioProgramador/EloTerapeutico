# Finances

Domínio financeiro operacional da atividade clínica do profissional. O pacote Python oficial é `apps.finances`, enquanto o app label histórico do Django permanece `financeiro`.

## Fronteira com billing

`apps.finances` controla receitas, despesas, pagamentos, cobranças de consultas e mensalidades de pacientes. `apps.billing` controla planos, checkout, assinatura SaaS e integrações comerciais do Elo Terapêutico.

## Estrutura

- `api/v1`: filtros, permissões, serializers e views HTTP;
- `models`: schema histórico de transações e mensalidades;
- `selectors`: consultas reutilizáveis e isolamento multi-tenant;
- `services`: casos de uso transacionais;
- `integrations`: fronteira explícita com scheduling;
- `admin`: configuração Unfold por entidade;
- `tests`: contratos de API, services, selectors, integrações e arquitetura.

## Contratos preservados

- app label, tabelas, ContentTypes e permissões continuam usando `financeiro`;
- migrations históricas não são reescritas;
- relações persistidas como `financeiro.MonthlySubscription` continuam válidas;
- identificadores de comunicação continuam como `financeiro.FinancialTransaction`;
- o nome visual permanece “Financeiro”;
- a API canônica é `/api/v1/finances/`.

## Regras essenciais

Pagamentos, cancelamentos, estornos, criação de mensalidades e geração de cobranças são atômicos e centralizados em services. Views e serializers não acessam ORM. A cobrança por consulta é idempotente e protegida pela constraint histórica.

## Validação

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python apps/core/quality/check_backend_architecture.py
pytest apps/finances -v
```
