# Padrão arquitetural dos apps Django

Este documento define a organização padrão dos apps do backend. O objetivo é manter as regras de negócio, consultas, API, integrações e processamento assíncrono em camadas previsíveis, sem obrigar apps pequenos a criarem pastas vazias.

## Estrutura de referência

```text
app_name/
├── __init__.py
├── apps.py
├── urls.py
├── constants.py
├── exceptions.py
├── models/
├── services/
├── selectors/
├── api/
│   ├── v1/
│   │   ├── urls.py
│   │   ├── serializers/
│   │   ├── views/
│   │   ├── permissions/
│   │   └── filters/
│   └── public/
├── integrations/
├── infrastructure/
├── tasks/
├── signals/
├── validators/
├── admin/
├── management/commands/
├── migrations/
└── tests/
```

A estrutura é proporcional ao tamanho do app. Um app pequeno pode manter um único arquivo por camada; um app complexo deve dividir os arquivos por entidade ou caso de uso.

## Responsabilidade das camadas

### Models

Contêm entidades, relacionamentos, constraints, índices, managers, querysets e métodos curtos que pertencem ao estado da entidade. Models não chamam APIs externas, não conhecem HTTP e não executam tarefas assíncronas.

Quando um app possui várias entidades, `models` deve ser um pacote dividido por contexto. O `models/__init__.py` expõe o contrato público sem alterar o app label, os nomes das tabelas ou as migrations históricas.

### Services

Implementam casos de uso que alteram estado ou coordenam operações. Services recebem dados do domínio, usam transações quando necessário e não dependem de `Request`, `Response` ou serializers.

### Selectors

Concentram consultas somente de leitura, incluindo filtros de tenant, `select_related`, `prefetch_related`, anotações e agregações. Selectors não alteram dados.

### API

A camada `api/v1` contém serializers, permissions, filters, views e URLs autenticadas. A camada `api/public` contém endpoints sem sessão. Views devem validar a entrada, chamar services/selectors e construir a resposta HTTP.

### Integrations

Contêm contratos e implementações de serviços externos, como e-mail, WhatsApp, SMS, gateways e processadores de webhook. Exceções de bibliotecas externas devem ser convertidas em exceções próprias da integração.

### Infrastructure

Contém detalhes técnicos internos, como mensageria, armazenamento, locks, adapters e clients HTTP. Regras de negócio não pertencem à infrastructure.

### Tasks

Tasks Celery são entradas assíncronas finas. Elas chamam services ou integrações, preservam idempotência e mantêm nomes explícitos quando esses nomes fazem parte da configuração externa.

### Signals

Signals apenas detectam eventos e delegam a services. O registro ocorre por meio do `AppConfig.ready()`. Processamento pesado e chamadas externas síncronas não devem ficar nos handlers.

### Validators

Contêm validações reutilizáveis do domínio. Validação estritamente ligada a um payload pode permanecer no serializer; validação compartilhada deve ser extraída.

### Admin

Apps com vários models devem dividir o admin por domínio ou entidade. O `admin/__init__.py` importa os módulos de registro para preservar o autodiscovery do Django.

## Direção das dependências

```text
API/views → serializers/permissions → services/selectors → models
services → integrations/infrastructure
signals/tasks/commands → services/integrations
```

Regras obrigatórias:

- models não importam API, serializers, views, tasks ou signals;
- services não dependem de objetos HTTP;
- selectors não importam views e não alteram estado;
- tasks e signals não duplicam regras existentes em services;
- integrações não importam views;
- views autenticadas não acessam o ORM diretamente quando existe selector ou service apropriado;
- imports com `*` são proibidos;
- ciclos não devem ser escondidos com imports locais sem correção arquitetural.

## Compatibilidade durante refatorações

Quando um caminho antigo já é usado pelo projeto, o arquivo pode permanecer temporariamente como fachada fina, contendo somente imports e `__all__`. A implementação deve existir apenas no novo pacote.

Exemplo:

```python
from .api.v1.permissions import CanAccessCommunications

__all__ = ["CanAccessCommunications"]
```

Fachadas devem ser removidas apenas quando todos os consumidores estiverem migrados e a mudança puder ser feita sem quebrar contratos internos, configurações, imports de terceiros ou pontos de monkeypatch da suíte.

## Migrations históricas

Arquivos importados por migrations históricas mantêm seu caminho original. No app `communications`, `migration_operations.py` permanece na raiz para garantir que bancos novos e migrations antigas continuem funcionando. Migrations aplicadas não devem ser reescritas por motivos puramente organizacionais.

Mover um `models.py` para `models/` é permitido quando as classes continuam pertencendo ao mesmo app Django, com os mesmos nomes, campos, constraints, índices e tabelas.

## Como dividir arquivos

Arquivos entre aproximadamente 250 e 350 linhas devem ser revisados. A divisão é necessária quando o módulo contém entidades diferentes, múltiplos casos de uso, vários provedores, endpoints sem coesão ou responsabilidades que precisam de testes isolados. O número de linhas não é uma regra mecânica.

## Testes

Quando aplicável, organize os testes em:

```text
tests/
├── unit/
├── integration/
├── api/
├── factories/
└── conftest.py
```

- `unit`: services, validators e regras puras;
- `integration`: banco, providers, tasks, signals e infrastructure;
- `api`: rotas, autenticação, permissões e contratos HTTP.

Além dos testes funcionais, apps complexos devem ter testes de importação, contratos de URL, nomes de tasks, fachadas de compatibilidade e ausência de módulos monolíticos removidos.

## Referência: communications

O app `communications` é a referência para módulos orientados a comunicação e eventos:

- API versionada em `api/v1` e endpoints públicos em `api/public`;
- providers separados em `integrations/providers`;
- selectors divididos por contexto;
- tasks divididas por processo, com nomes Celery preservados;
- signals divididos pelo domínio de origem;
- validators e admin organizados em pacotes;
- arquivos antigos mantidos apenas quando necessários como fachadas de compatibilidade.

## Referência: billing

O app `billing` é a referência para módulos financeiros e integrações críticas:

- models divididos por catálogo, contratação, assinatura, pagamento, webhook e uso;
- API autenticada em `api/v1` e fluxos sem sessão em `api/public`;
- serializers e views separados por caso de uso;
- checkout e regras transacionais mantidos em services;
- client HTTP do Asaas isolado em `infrastructure/payments/asaas`;
- interpretação e persistência de webhooks em `integrations/webhooks/asaas`;
- tasks de webhook e reconciliação separadas, com nomes Celery preservados;
- admin dividido por contexto;
- fachadas antigas mantidas para URLs, autenticação, cadastro, imports e testes existentes;
- validações arquiteturais impedem o retorno de `models.py`, `admin.py` e `tasks.py` monolíticos.

## Criação de um novo app

1. identifique as entidades e os casos de uso;
2. crie somente as camadas realmente necessárias;
3. mantenha consultas reutilizáveis em selectors;
4. mantenha alterações de estado em services;
5. exponha a API por uma versão explícita;
6. isole integrações externas e normalize suas exceções;
7. adicione testes de importação e fronteiras arquiteturais;
8. documente qualquer exceção ao padrão.
