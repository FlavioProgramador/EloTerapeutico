# Mapa arquitetural do backend

## Princípio

Cada app mantém entrypoints convencionais do Django e expõe contratos públicos de forma explícita. Regras transacionais ficam em `services/`, consultas reutilizáveis e sensíveis ao proprietário ficam em `selectors/` ou `querysets/`, e a adaptação HTTP fica em `views/`, `serializers/`, `filters/` e `permissions/`.

Pastas são criadas apenas quando representam uma responsabilidade real. Diretórios genéricos como `model_parts/` e arquivos monolíticos como `core_services.py` não fazem parte da arquitetura aceita.

## Grafo de dependências

```text
URLs
  ↓
Views / ViewSets
  ↓
Serializers · Filters · Permissions
  ↓
Services · Selectors
  ↓
QuerySets / Managers
  ↓
Models
```

Integrações externas seguem o fluxo `View → Service → Gateway/Client`.

## Estrutura atual resumida

```text
backend/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── apps/
    ├── core/
    │   ├── api/
    │   ├── integrations/
    │   ├── quality/
    │   ├── exceptions.py
    │   ├── fields.py
    │   └── validators.py
    ├── users/
    │   ├── api/
    │   ├── services/
    │   ├── models.py
    │   └── urls.py
    ├── patients/
    │   ├── models/
    │   ├── actions/
    │   ├── api/
    │   ├── selectors/
    │   ├── services/
    │   └── tests/
    ├── records/
    │   ├── models/
    │   ├── api/
    │   ├── selectors/
    │   ├── services/
    │   ├── management/
    │   └── tests/
    ├── agenda/
    │   ├── models/
    │   ├── api/
    │   │   ├── serializers/
    │   │   └── views/
    │   ├── selectors/
    │   ├── services/
    │   │   ├── appointments.py
    │   │   ├── packages.py
    │   │   ├── recurrences.py
    │   │   ├── resources.py
    │   │   └── financial_sync.py
    │   ├── exceptions/
    │   └── tests/
    ├── documents/
    │   ├── models/
    │   ├── selectors/
    │   ├── services/
    │   ├── serializers/
    │   ├── views/
    │   ├── filters/
    │   ├── permissions/
    │   ├── exceptions/
    │   └── tests/
    ├── forms/
    │   ├── models/
    │   ├── api/
    │   └── tests/
    ├── financeiro/
    │   ├── models/
    │   ├── api/
    │   ├── selectors/
    │   ├── services/
    │   └── tests/
    ├── reports/
    │   ├── selectors/
    │   ├── services/
    │   ├── views/
    │   └── tests/
    ├── billing/
    │   ├── infrastructure/
    │   ├── services/
    │   └── tests/
    └── communications/
        ├── application/
        ├── domain/
        ├── infrastructure/
        └── tests/
```

`apps.scheduling.api` permanece como contrato público porque seus imports são cobertos por testes de arquitetura. O diretório contém somente adaptação HTTP; os casos de uso foram transferidos para `apps.scheduling.services`.

## Apps e responsabilidades consolidadas

### Documentos

- `models/`: templates, sequências e documentos gerados.
- `selectors/`: templates privados, biblioteca, documentos por proprietário e pacientes acessíveis.
- `services/document_templates.py`: criação, atualização, importação, duplicação e mudanças de estado.
- `services/generated_documents.py`: criação idempotente, snapshot, edição, arquivamento e cancelamento.
- `services/pdf_generation.py`: processamento, hash, assinatura e persistência privada do PDF.
- `services/sequences.py`: numeração concorrente com bloqueio de linha.
- `serializers/`, `views/`, `filters/`, `permissions/` e `exceptions/`: adaptação específica da API.

### Agenda

- `services/appointments.py`: criação, atualização, transições de status e cancelamento administrativo.
- `services/packages.py`: criação de pacote, cobrança vinculada, consumo, liberação e sincronização das sessões.
- `services/recurrences.py`: cálculo e materialização de recorrências.
- `services/resources.py`: lembretes e salas de telemedicina derivados da consulta.
- `services/financial_sync.py`: integração explícita entre consulta e lançamento financeiro.
- `selectors/appointments.py`: carregamento otimizado das relações usadas pela API.

### Relatórios

- `selectors/appointments.py`: consultas do terapeuta no período.
- `selectors/patients.py`: pacientes do proprietário.
- `selectors/financial_transactions.py`: transações, mensalidades e pacotes ativos do terapeuta.
- `services/appointment_reports.py`: KPIs e gráficos de agenda.
- `services/patient_reports.py`: retenção, risco de evasão e distribuição demográfica.
- `services/financial_reports.py`: inadimplência, DRE, convênios e projeção.
- `services/online_scheduling_reports.py`: contrato atual do relatório de agendamento online.
- `views/exports.py`: exportação CSV sem misturar o cálculo analítico.

### Pacientes

`apps.patients.services.lifecycle` controla desativação e restauração. `apps.patients.services.imports` valida e importa CSVs. Selectors restringem pacientes pelo profissional antes de resolver identificadores.

### Prontuário

`apps.records.services.evolutions` centraliza criação, atualização, versionamento, arquivamento e anexos. Selectors aplicam confidencialidade, autor e escopo clínico.

### Financeiro

`apps.financeiro.services.payments`, `cancellations`, `reversals` e `exports` centralizam mudanças de estado e exportações. Selectors aplicam visibilidade por função e terapeuta.

### Billing e integrações

A integração Asaas fica em `apps.billing.infrastructure.payments.asaas`. Views de billing não acessam diretamente o ORM nem a infraestrutura; services coordenam os casos de uso.

### Comunicações

O envio de e-mail é delegado a `apps.communications.infrastructure.messaging.email`. A aplicação controla fila, templates, automações e retentativas sem acoplar regras de domínio ao provider.

## Segurança e multi-tenant

- Templates e documentos gerados são filtrados pelo proprietário antes da busca por UUID.
- Pacientes são resolvidos pelo terapeuta autorizado.
- Consultas, pacotes e transações são limitados pelo escopo do profissional e da função.
- Relações recebidas em payload são validadas contra o mesmo proprietário.
- Evoluções confidenciais permanecem filtradas por autor ou permissão específica.
- Downloads validam vínculo e autorização antes de abrir o arquivo.
- Pagamentos, consultas, pacotes, recorrências e numeração documental usam transações e bloqueio de linha quando necessário.
- Auditoria permanece na borda HTTP e não registra conteúdo clínico completo.

## Compatibilidade

- Migrations históricas não foram reescritas.
- Classes, `app_label`, tabelas, constraints, índices e relações dos models foram preservados.
- Endpoints, nomes de rotas, status HTTP e formatos de resposta permanecem compatíveis.
- Imports públicos usam `__init__.py` explícitos e não utilizam `import *`.
- Não existe um segundo app genérico `core`.

## Validação automática

`apps.core.quality.check_backend_architecture` verifica:

- diretórios permitidos na raiz do backend;
- ausência de `model_parts/`;
- ausência de `core_services.py`;
- ausência de imports legados;
- presença das camadas canônicas de Documentos, Agenda e Relatórios;
- limites entre views de billing, ORM e infraestrutura.

O Django CI executa esse validador antes de `manage.py check`, verificação de migrations, pre-commit e testes.

## Referência completa

Consulte [`docs/backend-architecture.md`](../backend-architecture.md) para convenções, exemplos de fluxo, transações, criação de entidades, services, selectors e integrações.
