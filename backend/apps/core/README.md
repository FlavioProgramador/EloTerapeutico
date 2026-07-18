# App `core`

O app `core` concentra componentes técnicos e transversais utilizados por mais de um domínio do backend. Ele deve permanecer na base do grafo de dependências e não funcionar como depósito de regras de negócio.

## Responsabilidades

Podem permanecer no `core`:

- componentes compartilhados do Django REST Framework;
- paginação e tratamento global de exceções;
- campos Django reutilizáveis;
- validadores independentes de domínio;
- health checks técnicos;
- componentes comuns do Django Admin e Django Unfold;
- verificações arquiteturais do backend;
- modelos abstratos ou permissões técnicas realmente transversais.

Não devem permanecer no `core`:

- regras de pacientes, prontuário, agenda ou financeiro;
- regras de assinatura e cobrança;
- regras de comunicação ou notificações;
- queries específicas de um domínio;
- clientes de APIs externas;
- services utilizados por apenas um app;
- models pertencentes a outro domínio.

## Estrutura

```text
core/
├── admin/                  # Dashboard, SQL Explorer e configuração do Unfold
├── api/
│   ├── exceptions.py      # Handler global do DRF
│   ├── pagination.py
│   ├── urls.py
│   └── views/health.py    # Adaptação HTTP dos health checks
├── exceptions/            # Superfície pública de exceções compartilhadas
├── fields/                # Campos Django reutilizáveis
├── health/                # Checks técnicos e serviço agregador
├── quality/
│   ├── check_backend_architecture.py
│   ├── legacy_backend_architecture.py
│   └── rules/core.py
├── tests/
└── validators/            # Validadores independentes de domínio
```

Os arquivos `admin_dashboard.py` e `admin_sql.py` são aliases temporários para preservar callbacks configurados e pontos de patch existentes. Eles não podem voltar a receber implementação.

## Direção de dependências

O fluxo HTTP deve seguir:

```text
URLs → Views → Services/Componentes técnicos
```

Para apps de domínio, o padrão permanece:

```text
URLs → Views → Serializers/Permissions → Services/Selectors → Models
```

Fora da camada administrativa, o `core` não pode importar diretamente `billing`, `communications`, `patients`, `records`, `agenda`, `financeiro`, `documents`, `forms` ou `reports`.

## Imports públicos preservados

Os caminhos abaixo continuam válidos:

```python
from apps.core.exceptions import custom_exception_handler
from apps.core.fields import EncryptedTextField, decrypt_value, encrypt_value
from apps.core.validators import validate_cpf, validate_crp, validate_phone
from apps.core.health import liveness, readiness
```

As migrations antigas que referenciam `apps.core.fields` não precisam ser alteradas, pois o pacote mantém a mesma API pública.

## Health checks

- `/health/live/`: confirma que o processo web está ativo;
- `/health/ready/`: verifica banco, Redis e, quando habilitado, storage;
- os payloads, nomes das rotas e status HTTP anteriores foram preservados;
- views HTTP ficam em `api/views/health.py`;
- checks técnicos ficam em `health/checks.py`;
- agregação fica em `health/services.py`.

## Verificação arquitetural

Execute a partir de `backend/`:

```bash
python apps/core/quality/check_backend_architecture.py
pytest apps/core/tests -v
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
mypy .
python manage.py spectacular --file schema.yml --validate
```

O verificador principal executa primeiro as regras específicas do `core` e depois todas as regras anteriores de billing, communications e organização geral do backend.

## Checklist antes de adicionar código ao core

- O recurso é utilizado por mais de um app?
- Ele é independente de regras de domínio?
- O app consumidor seria um local mais adequado?
- A mudança cria dependência do `core` para um app de negócio?
- O componente deveria ser um validator, campo, serviço técnico ou adaptação HTTP?
- Existe risco de criar um novo arquivo monolítico?
- A API pública e os efeitos colaterais estão documentados?
- Existem testes isolados e uma regra arquitetural aplicável?
- Migrations, endpoints e imports históricos permanecem compatíveis?
