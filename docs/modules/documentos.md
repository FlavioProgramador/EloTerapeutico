# Módulo de Documentos

## Objetivo

O módulo centraliza templates de documentos, biblioteca global, geração de PDFs e templates de evolução. O conteúdo clínico e os snapshots usados na emissão são criptografados com o campo seguro já adotado pelo projeto.

## Escopo de isolamento

O projeto ainda não possui uma entidade `Clinic`. Por isso, o isolamento desta implementação segue o contrato efetivo do sistema: cada profissional é o tenant dos seus templates, pacientes e documentos. A API nunca aceita `owner`, `professional` ou escopo enviados pelo cliente; esses valores são derivados do usuário autenticado.

Usuários com papel de secretária não acessam o módulo clínico. Templates globais possuem `owner = NULL`, são somente leitura para usuários comuns e precisam ser importados antes do uso.

## Entidades

### `DocumentTemplate`

- `public_id` UUID para exposição na API;
- proprietário ou escopo global da biblioteca;
- tipo, categoria, especialidade e status;
- conteúdo, cabeçalho e rodapé criptografados;
- versão, contador de uso, origem da biblioteca e soft archive.

### `GeneratedDocument`

- vínculo autorizado com paciente e profissional;
- número transacional por profissional e ano;
- snapshot completo do template e das configurações de emissão;
- contexto criptografado com apenas variáveis permitidas;
- HTML sanitizado, PDF privado, SHA-256 e hash de assinatura;
- estados: rascunho, processando, concluído, falhou, cancelado e arquivado.

### `DocumentSequence`

Controla a numeração `DOC-AAAA-000000` com bloqueio transacional.

## Variáveis permitidas

O renderizador não usa `eval`, acesso dinâmico a atributos ou templates Django. Somente os marcadores retornados por `GET /api/v1/documents/placeholders/` são aceitos.

Grupos disponíveis:

- paciente: nome, nome completo, nome social, CPF, data de nascimento, idade e responsável;
- profissional: nome, registro e especialidade;
- clínica: nome, endereço e telefone configurados no ambiente;
- documento: data, local de emissão e número.

HTML bruto é escapado. O Markdown suportado é deliberadamente limitado a títulos, listas, negrito, itálico e `[[QUEBRA_DE_PAGINA]]`.

## Endpoints

Base: `/api/v1/documents/`

- `templates/`: CRUD, filtros, preview, duplicação, ativação, inativação e arquivamento;
- `library/`: listagem, preview e importação idempotente;
- `generated/`: criação de rascunho, filtros, geração, download autenticado, cancelamento e arquivamento;
- `placeholders/`: catálogo da whitelist.

Templates de evolução permanecem no domínio do prontuário:

- `GET|POST /api/v1/records/clinical-templates/`;
- `GET|PATCH|DELETE|POST /api/v1/records/clinical-templates/{id}/`.

O `POST` de detalhe aceita as ações `duplicate`, `activate`, `deactivate`, `archive` e `mark_used`.

## Geração de PDF

A implementação reutiliza WeasyPrint, já presente no projeto. A geração é síncrona e não cria threads dentro da requisição. O status é persistido antes do processamento; falhas deixam o documento em `failed` com mensagem sanitizada.

Quando o projeto adotar um worker assíncrono, o serviço `generate_pdf` é o ponto de extração para a fila. O snapshot garante que alterações futuras no template não modifiquem documentos já emitidos.

Downloads são servidos por `FileResponse`, após autorização por objeto, com `Cache-Control: private, no-store` e sem exposição da URL direta do storage.

## Configuração opcional

```env
DOCUMENT_CLINIC_NAME=Elo Terapêutico
DOCUMENT_CLINIC_ADDRESS=
DOCUMENT_CLINIC_PHONE=
```

## Migrations e biblioteca

```bash
cd backend
python manage.py migrate
```

A migration `documents.0002_seed_library` cria modelos globais iniciais de forma idempotente.

## Validação

```bash
cd backend
python manage.py test apps.documents apps.records
python manage.py check
python manage.py makemigrations --check

cd ../frontend
npm run lint
npm run build
```

## Auditoria

O módulo reutiliza `apps.core.audit` e registra criação, edição, importação, preview, geração, download, cancelamento e arquivamento. O conteúdo clínico completo não é gravado na descrição do log.

## Limitações deliberadas

- não há assinatura digital qualificada; é armazenado um hash de integridade e o snapshot do profissional;
- a geração permanece síncrona porque o repositório não possui fila de tarefas configurada;
- o isolamento usa o profissional como tenant até existir um modelo de clínica compartilhada.
