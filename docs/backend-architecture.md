# Arquitetura do backend

Este documento define a organização canônica do backend Django do EloTerapêutico. O objetivo é manter regras de negócio previsíveis, consultas seguras por tenant, contratos HTTP estáveis e módulos testáveis de forma isolada.

## Fluxo de dependências

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

Integrações externas são chamadas somente a partir de services ou de módulos de infraestrutura:

```text
View → Service → Gateway / Client externo
```

Dependências no sentido inverso são proibidas. Models não importam views, serializers ou services. Services não recebem `request` e não retornam `Response`.

## Estrutura de um app

Cada app possui somente as camadas necessárias ao próprio domínio. Não devem ser criadas pastas vazias apenas para reproduzir um padrão.

```text
app_name/
├── models/
├── querysets/
├── selectors/
├── services/
├── serializers/
├── views/
├── filters/
├── permissions/
├── exceptions/
├── tasks/
├── signals/
├── tests/
├── admin.py
├── apps.py
└── urls.py
```

Alguns apps ainda mantêm adaptadores em `api/` quando esse caminho já faz parte de imports públicos testados. Nesses casos, `api/` deve conter somente adaptação HTTP; regras de negócio e consultas reutilizáveis permanecem em `services/` e `selectors/`.

## Responsabilidades por camada

### Models

Models contêm campos, relações, constraints, índices, propriedades simples e operações estritamente ligadas ao estado da própria entidade. Eles não enviam e-mails, não chamam gateways, não criam fluxos com diversos agregados e não conhecem HTTP.

Apps com múltiplas entidades utilizam pacotes `models/` com exportação explícita em `models/__init__.py`. A reorganização de arquivos não altera `app_label`, nomes de tabela ou migrations históricas.

### QuerySets e managers

QuerySets encapsulam filtros reutilizáveis e regras recorrentes de visibilidade, como:

```python
Model.objects.owned_by(user)
Model.objects.for_tenant(tenant)
Model.objects.active()
Model.objects.visible_to(user)
```

Filtros de tenant não devem ser repetidos em várias views.

### Selectors

Selectors são somente leitura. Eles encapsulam consultas complexas, `select_related`, `prefetch_related`, agregações e escopo multi-tenant.

Exemplos atuais:

- `apps.documents.selectors.document_templates`
- `apps.documents.selectors.generated_documents`
- `apps.reports.selectors.appointments`
- `apps.reports.selectors.financial_transactions`
- `apps.scheduling.selectors.appointments`
- `apps.patients.selectors.patients`
- `apps.financeiro.selectors.transactions`

Um selector nunca altera dados.

### Services

Services representam casos de uso e regras de negócio. Devem utilizar argumentos nomeados, transações quando necessário e exceções de domínio explícitas.

Exemplos atuais:

- `apps.documents.services.document_templates`
- `apps.documents.services.generated_documents`
- `apps.documents.services.pdf_generation`
- `apps.scheduling.services.appointments`
- `apps.scheduling.services.packages`
- `apps.scheduling.services.recurrences`
- `apps.reports.services.financial_reports`
- `apps.financeiro.services.payments`

Operações que modificam vários registros usam `transaction.atomic`. Operações concorrentes utilizam `select_for_update()` quando há risco real de disputa. Chamadas lentas de rede não devem permanecer dentro de transações longas.

### Serializers

Serializers validam payloads, convertem dados e produzem representações. Eles podem delegar a criação ou atualização para um service, mas não devem implementar transações extensas, cobrança, envio de mensagens, geração de arquivos ou acesso complexo entre tenants.

### Views

Views tratam autenticação, permissão, parsing, filtros, paginação, seleção do serializer, chamada do caso de uso e resposta HTTP. Auditoria permanece na borda HTTP quando depende do contexto da requisição.

### Filters

Todos os `FilterSet` ficam em módulos próprios por entidade. Filtros não devem ser declarados dentro de views.

### Permissions

Permissões de domínio ficam em `permissions/`. Verificações de propriedade repetidas não devem aparecer em diversas actions.

### Exceptions

Cada app pode possuir exceções específicas. Exceções compartilhadas utilizam a infraestrutura já aprovada em `apps.core`; não deve ser criado outro app genérico `core`.

### Tasks e signals

Tasks recebem identificadores simples, recuperam os dados necessários e chamam services. Signals permanecem mínimos e não ocultam casos de uso importantes.

## Exemplo completo: geração de documento

```text
POST /api/v1/documents/generated/
  ↓
GeneratedDocumentViewSet.create
  ↓
GeneratedDocumentCreateSerializer
  ↓
selectors.get_owned_template + selectors.get_accessible_patient
  ↓
services.create_generated_document
  ↓
services.reserve_document_number
  ↓
GeneratedDocument.objects.create
  ↓
GeneratedDocumentDetailSerializer
  ↓
HTTP 201 ou HTTP 200 para repetição idempotente
```

O ViewSet não cria registros diretamente. O serializer valida o payload e resolve objetos já limitados ao terapeuta. O service controla transação, idempotência, snapshot e numeração.

## Isolamento multi-tenant

Toda leitura, atualização ou exclusão deve restringir o conjunto de dados antes de buscar por ID ou UUID.

Regras obrigatórias:

- pacientes pertencem ao terapeuta autorizado;
- templates privados pertencem ao proprietário;
- documentos gerados são filtrados por `owner`;
- consultas são limitadas pelo escopo da Agenda;
- transações financeiras são limitadas pelo terapeuta e função;
- relações recebidas no payload também devem pertencer ao mesmo tenant;
- nenhum endpoint usa `Model.objects.get(pk=...)` sem escopo quando o identificador vem do cliente.

Testes devem cobrir leitura, alteração, exclusão e relacionamento cruzado entre tenants.

## Transações e concorrência

Use `transaction.atomic` para:

- criação de consultas e recorrências;
- consumo e liberação de sessões de pacote;
- sincronização entre Agenda e Financeiro;
- geração e mudança de estado de documentos;
- pagamentos, cancelamentos e estornos;
- criação de paciente com relações;
- processamento idempotente de webhooks.

Use `select_for_update()` em sequências, saldos, estados concorrentes, pagamentos, pacotes e consultas que podem ser alteradas simultaneamente.

## Integrações externas

Clientes de Asaas, e-mail, armazenamento e outros providers ficam em infraestrutura ou gateways explícitos. Services convertem erros externos em exceções internas e não expõem o formato bruto do provider à API.

## Como adicionar uma nova entidade

1. Crie o model no arquivo de entidade dentro de `models/`.
2. Exporte somente o contrato público em `models/__init__.py`.
3. Adicione QuerySet ou manager quando existirem filtros reutilizáveis.
4. Crie selectors para leituras complexas ou multi-tenant.
5. Implemente casos de uso em services com argumentos nomeados.
6. Crie serializers separados para entrada e saída quando os contratos forem diferentes.
7. Adicione filters e permissions específicos quando necessários.
8. Mantenha a view fina e preserve os nomes públicos das rotas.
9. Adicione testes de model, selector, service, serializer e endpoint.
10. Execute checks, migrations, lint e toda a suíte.

## Como adicionar um service

Um service deve expressar o caso de uso no nome:

```python
@transaction.atomic
def activate_subscription(*, user, plan, payment_data):
    ...
```

Evite nomes genéricos como `process`, `handle`, `core_services`, `utils` ou `helpers` quando o domínio puder ser descrito explicitamente.

## Como adicionar um selector

```python
def generated_documents_for_owner(*, owner):
    return GeneratedDocument.objects.filter(owner=owner).select_related(
        "patient",
        "professional",
        "template",
    )
```

Selectors não recebem `request`, não escrevem no banco e não retornam `Response`.

## Imports públicos

Pacotes exportam explicitamente seus elementos públicos:

```python
from .generated import GeneratedDocument
from .templates import DocumentTemplate

__all__ = ["GeneratedDocument", "DocumentTemplate"]
```

`import *` é proibido. Arquivos antigos devem ser removidos depois que todos os consumidores forem migrados. Compatibilidade temporária só é aceita quando um caminho está comprovadamente serializado em migrations ou coberto como contrato público.

## Compatibilidade e migrations

A movimentação de módulos Python não deve gerar migrations. Não altere migrations históricas aplicadas. Os comandos de validação são:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
ruff check .
mypy .
docker compose config
```

Ferramentas somente são executadas quando já estão configuradas no projeto.

## Revisão arquitetural automatizada

`backend/apps/core/quality/check_backend_architecture.py` impede o retorno de diretórios `model_parts/`, arquivos `core_services.py`, imports legados e infraestrutura em locais não aprovados. A verificação faz parte do Django CI.
