# Evoluções Clínicas

## Visão geral

O fluxo de evolução clínica utiliza um modal responsivo dentro do prontuário do paciente. O modal atende criação e edição, mantém o usuário na página atual e atualiza apenas as consultas do React Query relacionadas ao prontuário.

## Fluxo da interface

O modal contém:

- vínculo opcional com uma consulta do paciente;
- data obrigatória do atendimento;
- editor Markdown seguro;
- seleção de templates do profissional ou da clínica;
- opção de confidencialidade;
- anexos protegidos;
- rodapé fixo com cancelamento e gravação.

A consulta selecionada preenche a data automaticamente. Quando a data é alterada manualmente para um valor diferente, o usuário precisa confirmar a divergência antes de salvar.

O fechamento ocorre pelo botão de fechar, por `Escape`, pelo botão Cancelar ou pelo overlay. Alterações não salvas geram uma confirmação, e o modal não pode ser fechado durante o envio.

## Editor

O editor armazena Markdown, não HTML. O conteúdo é sanitizado no backend antes da persistência e também é escapado durante a renderização.

Recursos disponíveis:

- negrito;
- itálico;
- lista com marcadores;
- lista numerada;
- desfazer e refazer;
- contador de caracteres.

O conteúdo clínico não é salvo em `localStorage` nem enviado por notificações, e-mail ou WhatsApp.

## Templates

Os templates são armazenados em `ClinicalEvolutionTemplate`.

- templates pessoais possuem `owner`;
- templates globais possuem `owner = null`;
- apenas usuários com a permissão `records.manage_system_clinical_templates` podem alterar templates globais;
- secretárias não acessam templates clínicos;
- o conteúdo é criptografado em repouso.

Endpoints:

```text
GET    /api/v1/records/clinical-templates/
POST   /api/v1/records/clinical-templates/
PATCH  /api/v1/records/clinical-templates/{id}/
DELETE /api/v1/records/clinical-templates/{id}/
```

## Confidencialidade

Uma evolução confidencial é visível somente para:

- o autor;
- superusuários;
- usuários com `records.view_confidential_evolution`.

O papel administrativo, isoladamente, não concede acesso ao conteúdo confidencial. Secretárias permanecem bloqueadas de todo o conteúdo clínico.

Criação, alteração da confidencialidade, visualização, arquivamento e acesso a anexos são registrados em auditoria sem copiar o texto clínico para logs comuns.

## Consultas vinculadas

O endpoint de opções retorna somente consultas do paciente autorizado:

```text
GET /api/v1/records/patients/{patient_id}/evolution-appointments/
```

O backend valida novamente:

- paciente da URL;
- paciente da consulta;
- profissional autorizado;
- status da consulta;
- uso anterior do vínculo.

Essa validação impede IDOR mesmo quando o identificador da consulta é alterado manualmente na requisição.

## Anexos

Formatos permitidos:

- JPG e JPEG;
- PNG;
- GIF;
- WebP;
- PDF.

O limite padrão é de 10 MB por arquivo e 10 arquivos por evolução. Os valores podem ser configurados por:

```text
CLINICAL_ATTACHMENT_MAX_BYTES
CLINICAL_EVOLUTION_MAX_ATTACHMENTS
```

A validação verifica:

- tamanho;
- extensão;
- MIME declarado;
- assinatura real do arquivo;
- nome de exibição sanitizado.

Os arquivos utilizam nomes físicos UUID, não possuem URL pública e são entregues somente por views autenticadas com autorização clínica.

Endpoints:

```text
GET    /api/v1/records/clinical-evolutions/{id}/attachments/
POST   /api/v1/records/clinical-evolutions/{id}/attachments/
DELETE /api/v1/records/clinical-evolutions/{id}/attachments/{attachment_id}/
GET    /api/v1/records/clinical-evolutions/{id}/attachments/{attachment_id}/download/
```

## Datas retroativas

Datas futuras são rejeitadas. Por padrão, terapeutas podem registrar evoluções em até sete dias retroativos. Registros anteriores exigem:

- administrador;
- superusuário;
- ou a permissão `records.add_retroactive_evolution` quando disponibilizada pela instalação.

O limite pode ser alterado com `CLINICAL_RETROACTIVE_WINDOW_DAYS`.

## Edição e versionamento

O mesmo modal é utilizado para criação e edição.

A edição direta exige:

- autoria do registro;
- evolução em rascunho;
- janela de edição ainda aberta;
- evolução não bloqueada.

Antes de cada edição é criada uma `EvolutionVersion` com o estado anterior. O conteúdo da versão permanece criptografado.

A exclusão disponível pela API é lógica: o registro passa para o estado `archived` e permanece disponível para auditoria.

## Endpoints de evolução

```text
POST   /api/v1/records/patients/{patient_id}/clinical-evolutions/
GET    /api/v1/records/patients/{patient_id}/clinical-evolutions/
GET    /api/v1/records/clinical-evolutions/{id}/
PATCH  /api/v1/records/clinical-evolutions/{id}/
DELETE /api/v1/records/clinical-evolutions/{id}/
```

## Validação

Backend:

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend pytest apps/records -q
docker compose exec backend pytest apps/patients -q
```

Frontend:

```bash
docker compose exec frontend npm run lint
docker compose exec frontend npx tsc --noEmit
docker compose exec frontend npm run build
```

## Integrações futuras

A validação atual bloqueia arquivos executáveis e tipos não permitidos. Uma etapa de antivírus ou análise assíncrona pode ser adicionada antes de disponibilizar o download quando a infraestrutura oferecer um serviço de varredura.
