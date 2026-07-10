# Módulo de documentos

**Status: implementado.**

## Finalidade

Criar modelos reutilizáveis, disponibilizar biblioteca global e gerar documentos associados a pacientes com snapshots e verificação de integridade.

## Entidades

### DocumentTemplate

- UUID público;
- proprietário ou biblioteca global;
- nome, descrição, categoria, tipo e especialidade;
- conteúdo, cabeçalho e rodapé criptografados;
- flags de identificação e assinatura;
- status ativo, inativo ou arquivado;
- versão, uso e auditoria de autoria.

Tipos: declaração, relatório, encaminhamento, atestado, consentimento e outro.

### GeneratedDocument

Snapshot de template, profissional, paciente, conteúdo renderizado e contexto. Status: rascunho, processando, concluído, falhou, cancelado ou arquivado. Possui número por proprietário, hash SHA-256, assinatura, idempotência e PDF.

### DocumentSequence

Controla numeração conforme implementação do domínio.

## Regras

- template privado exige owner; template de biblioteca exige owner nulo;
- nomes ativos são únicos por proprietário e na biblioteca;
- gestão da biblioteca exige permissão `manage_document_library`;
- documentos gerados preservam snapshots mesmo que o template mude;
- idempotency key é única por owner quando informada;
- PDFs podem ter hash de integridade;
- arquivamento não remove histórico.

## API

Prefixo `/api/v1/documents/`:

- `templates/`;
- `library/`;
- `generated/`;
- `placeholders/`.

ViewSets expõem actions de geração, importação de biblioteca, download, assinatura ou arquivamento conforme schema OpenAPI.

## Frontend

Rota `/dashboard/documentos` e feature associada oferecem biblioteca, modelos e documentos gerados.

## Segurança

- conteúdos e snapshots textuais usam criptografia de campo;
- downloads devem validar owner/paciente;
- placeholders não podem permitir execução de código;
- HTML/PDF deve ser sanitizado;
- storage deve ser privado;
- hashes detectam alteração, mas não substituem assinatura digital qualificada.

## Testes e limitações

Existem testes no domínio de documentos e segurança clínica. Assinatura por hash não deve ser divulgada como certificado ICP-Brasil sem implementação específica. A configuração da identidade da clínica é operacional.

[Voltar aos módulos](../README.md)
