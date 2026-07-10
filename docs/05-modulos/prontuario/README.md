# Módulo de prontuário

**Status: implementado, com componentes parcialmente dependentes de configuração.**

## Finalidade

Organizar informações clínicas do paciente: anamnese, evoluções, dados estruturados, versões, aditivos, metas, documentos, anexos, formulários e exportações.

## Entidades

- `Anamnesis` e `AnamnesisProfile`;
- `AnamnesisVersion` e `EvolutionVersion`;
- `Evolution` e `EvolutionClinicalData`;
- `EvolutionAddendum`;
- `TreatmentGoal`;
- `ClinicalDocument`;
- `ClinicalFormResponse`;
- `ClinicalExport`;
- templates e anexos de evolução em módulos auxiliares.

## Regras de negócio

### Evoluções

- conteúdo principal usa `EncryptedTextField`;
- pode vincular uma única consulta;
- não aceita data futura;
- lançamentos retroativos além de sete dias exigem administrador/superusuário ou permissão explícita;
- pode ser editada por até 48 horas desde a criação, salvo bloqueio anterior;
- após bloqueio, correções devem ocorrer por aditivo;
- evolução confidencial só é visível ao autor ou a usuário/grupo com permissão explícita `view_confidential_evolution`;
- superusuário não recebe bypass automático na função de confidencialidade;
- exportação confidencial possui permissão separada.

### Conteúdo e uploads

- Markdown clínico é normalizado, HTML removido e esquemas executáveis eliminados;
- limite padrão de conteúdo: 50 mil caracteres;
- anexos padrão: até dez, cada um até 10 MB;
- extensões: JPEG, PNG, GIF, WebP e PDF;
- extensão, MIME declarado e assinatura do arquivo precisam corresponder;
- nomes originais são sanitizados; o nome físico usa caminho controlado.

### Exportações

- criação gera `ClinicalExport` em `PENDING`;
- worker reserva com lock, aplica filtro de confidencialidade, gera PDF e salva;
- estados: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `EXPIRED`;
- jobs presos há mais de dez minutos são recuperados;
- máximo de três tentativas no fluxo atual.

## API principal

Prefixo `/api/v1/records/`:

- `patients/{id}/workspace/`;
- `patients/{id}/clinical-anamnesis/` e `anamnesis-versions/`;
- `patients/{id}/clinical-evolutions/`;
- `clinical-evolutions/{id}/`, `/finalize/`, `/duplicate/`;
- anexos de evolução e download;
- `patients/{id}/goals/` e `goals/{id}/`;
- `patients/{id}/documents/`, detalhe e download;
- `patients/{id}/forms/` e detalhe;
- `patients/{id}/exports/`, retry e download;
- `patients/{id}/export-pdf/`;
- templates clínicos;
- endpoint de status/resumo de IA;
- router legado `evolutions/`.

## Frontend

`features/records` possui abas e componentes para anamnese, evoluções, agendamentos, metas, documentos, anexos e exportações. O prontuário é acessado no contexto do paciente.

## Permissões

- secretárias são bloqueadas das rotas de prontuário na navegação e precisam ser recusadas no backend;
- acesso a paciente não implica acesso a evolução confidencial;
- downloads e exports repetem autorização e registram auditoria;
- permissões explícitas são preferidas a role administrativa global em dados confidenciais.

## Auditoria

Visualizações, criações, atualizações, exclusões lógicas e exportações sensíveis devem usar `AuditLog`. A representação padrão registra apenas app/modelo e ID.

## Testes

Há testes de workspace, confidencialidade, exportações, documentos, uploads, headers de download, modal de evolução, templates, segurança de views legadas e administração.

## Limitações e riscos

- storage privado depende de configuração;
- não há antivírus;
- falha ao gravar auditoria não bloqueia a ação;
- IA aparece como indisponível no dashboard quando não configurada e não deve gerar decisão autônoma;
- expiração e retenção de exportações precisam de política operacional;
- proteção criptográfica depende da guarda e rotação da chave.

Implementação relacionada: `backend/apps/records/` e `frontend/src/features/records/`.

[Voltar aos módulos](../README.md)
