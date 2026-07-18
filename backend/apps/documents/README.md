# App Documents

O app `documents` concentra o domínio de templates, biblioteca documental, geração de documentos clínicos, snapshots, numeração, PDF, integridade e download privado.

## Responsabilidades

O módulo é responsável por:

- templates privados de profissionais;
- biblioteca global de templates;
- importação e duplicação de templates;
- documentos gerados e seus snapshots;
- sequência anual de numeração por proprietário;
- catálogo e renderização segura de placeholders;
- geração e persistência de PDF;
- hashes de integridade e assinatura interna;
- download privado;
- arquivamento, cancelamento e transições de estado;
- isolamento por owner e paciente;
- auditoria das operações HTTP e administrativas.

O módulo não deve assumir responsabilidades de autenticação, cadastro de pacientes, prontuário, cobrança, comunicações ou storage global da plataforma.

## Estrutura

```text
apps/documents/
├── admin/                 # Registros do Django Admin separados por model
├── api/v1/                # Contrato HTTP versionado
│   ├── permissions/
│   ├── serializers/
│   ├── views/
│   └── urls.py
├── exceptions/            # Exceções seguras do domínio
├── filters/               # Filtros da API
├── infrastructure/pdf/    # Adapter técnico do renderer de PDF
├── models/                # Persistência por entidade
├── selectors/             # Consultas de leitura e ownership
├── services/              # Casos de uso e transições de estado
├── tests/                 # Testes funcionais, de segurança e arquitetura
├── permissions/           # Fachada temporária de compatibilidade
├── serializers/           # Fachada temporária de compatibilidade
├── views/                 # Fachada temporária de compatibilidade
└── urls.py                # Fachada temporária para api.v1.urls
```

As fachadas antigas não contêm implementação e existem apenas para preservar imports públicos durante a migração.

## Direção de dependências

Fluxo HTTP:

```text
URLs
  ↓
Views
  ↓
Serializers / Permissions
  ↓
Services / Selectors
  ↓
Models
```

Fluxo de PDF:

```text
View
  ↓
Service de geração
  ↓
Composição de HTML sanitizado
  ↓
Adapter infrastructure/pdf
  ↓
WeasyPrint ou fallback controlado
```

Não são permitidos:

- ORM direto nas views;
- exclusão direta de models nas views;
- importação de infraestrutura por views ou serializers;
- imports de API a partir de models, selectors ou services;
- regras de ownership baseadas apenas em IDs enviados pelo frontend.

## API

O caminho canônico é:

```python
apps.documents.api.v1
```

O prefixo público permanece:

```text
/api/v1/documents/
```

Rotas principais:

- `templates/` — templates privados;
- `library/` — biblioteca global;
- `generated/` — documentos gerados;
- `placeholders/` — catálogo permitido de placeholders.

Os basenames, actions, métodos HTTP, payloads e códigos de resposta devem permanecer compatíveis com o schema OpenAPI.

## Models

### DocumentTemplate

Representa um template privado ou global. Templates privados possuem owner; templates de biblioteca possuem owner nulo e `is_library_template=True`.

### GeneratedDocument

Preserva snapshots do template, profissional, contexto e conteúdo renderizado. Os estados existentes são:

- `draft`;
- `processing`;
- `completed`;
- `failed`;
- `cancelled`;
- `archived`.

### DocumentSequence

Controla a sequência anual por owner. A reserva utiliza transação atômica e `select_for_update`, mantendo o formato:

```text
DOC-AAAA-000000
```

## Selectors

Selectors são funções de leitura sem efeitos colaterais. Exemplos públicos:

```python
owned_templates(owner=...)
library_templates()
get_owned_template(owner=..., public_id=...)
generated_documents_for_owner(owner=...)
get_accessible_patient(owner=..., patient_id=...)
find_by_idempotency_key(owner=..., idempotency_key=...)
```

Todos os selectors que acessam dados privados devem receber owner ou actor explicitamente.

## Services

Services controlam criação, atualização e transições de estado. Exemplos:

```python
create_template(...)
update_template(...)
remove_or_archive_template(...)
create_generated_document(...)
update_document_draft(...)
remove_or_archive_document(...)
generate_pdf(...)
prepare_document_download(...)
```

A política de remoção é centralizada:

- template sem histórico pode ser excluído;
- template associado ou importado é arquivado;
- rascunho sem PDF pode ser excluído;
- documento com histórico é arquivado.

## Placeholders

Somente placeholders presentes na whitelist podem ser usados. O renderer não executa Python e não permite `eval`, `exec`, acesso arbitrário a atributos ou HTML bruto.

A prévia e a geração final utilizam o mesmo mecanismo de validação e renderização segura.

## PDF

`services/pdf_generation.py` controla:

- bloqueio pessimista;
- transição para processamento;
- registro de falha;
- geração de hash;
- assinatura interna;
- persistência do arquivo;
- conclusão do documento.

`infrastructure/pdf/renderer.py` recebe HTML previamente sanitizado e apenas o converte em bytes de PDF.

O hash SHA-256 representa integridade técnica. Ele não equivale a certificado digital ICP-Brasil.

## Segurança

- conteúdo e snapshots sensíveis permanecem criptografados;
- downloads validam owner e estado do documento;
- arquivos são enviados com cache privado e `nosniff`;
- nomes de arquivo são derivados do número interno controlado;
- dados clínicos, tokens e conteúdo documental não devem aparecer em logs;
- secretárias não possuem acesso ao conteúdo clínico documental;
- templates e documentos de outro profissional devem retornar indisponíveis ou não autorizados.

## Compatibilidade

Os seguintes imports continuam disponíveis por fachadas finas:

```python
apps.documents.urls
apps.documents.permissions
apps.documents.serializers
apps.documents.views
```

Novos códigos devem preferir:

```python
apps.documents.api.v1.urls
apps.documents.api.v1.permissions
apps.documents.api.v1.serializers
apps.documents.api.v1.views
```

As fachadas não podem receber novas regras e devem permanecer pequenas.

## Testes

Executar:

```bash
cd backend
pytest apps/documents/tests -v
pytest apps/core/tests -v
python apps/core/quality/check_backend_architecture.py
python manage.py makemigrations --check --dry-run
```

Para validação completa:

```bash
pytest --create-db
ruff check .
mypy .
python manage.py spectacular --file schema.yml --validate
python -m compileall apps/documents
```

## Checklist antes de adicionar código ao documents

- O código pertence a template, documento gerado, sequência ou placeholder?
- É uma consulta de leitura ou uma alteração de estado?
- Deve ficar em selector ou service?
- Existe acesso direto ao ORM em uma view?
- O owner é recebido explicitamente?
- O paciente pertence ao profissional autenticado?
- O código manipula conteúdo clínico ou criptografado?
- A operação precisa de `transaction.atomic` ou `select_for_update`?
- O snapshot histórico permanece imutável?
- O renderer permite apenas placeholders autorizados?
- Há risco de path traversal ou exposição do storage?
- O hash está sendo tratado apenas como integridade técnica?
- O contrato da API e o schema OpenAPI foram preservados?
- Existem testes de ownership, estado e autorização?
- A nova dependência respeita a direção das camadas?
- O código está sendo colocado em uma fachada de compatibilidade? Se sim, mova-o para o caminho canônico.
