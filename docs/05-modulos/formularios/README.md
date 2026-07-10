# Módulo de formulários

**Status: implementado.**

## Finalidade

Permitir que o profissional construa formulários, reutilize templates, associe submissões a pacientes/consultas e armazene respostas estruturadas.

## Entidades

- `FormTemplate`;
- `TherapeuticForm`;
- `FormField`;
- `FormSubmission`;
- `FormAnswer`.

Formulários têm owner, categoria, descrição, status ativo/arquivado e origem opcional em template. Campos possuem tipo, label, placeholder, ajuda, obrigatoriedade, ordem, visibilidade, ID interno e configuração JSON.

Submissões têm status `draft`, `submitted`, `reviewed` ou `archived`, podendo referenciar paciente, profissional e consulta. Cada resposta é única por submissão e campo.

## Regras

- archive/restore atualizam autor e timestamp;
- submissão registra usuário e horário ao enviar;
- campos são ordenados por `order` e ID;
- configuração JSON deve ser validada pelo serializer;
- campos removidos não podem invalidar histórico protegido sem estratégia de versão;
- submissão enviada não deve ser alterada como se fosse rascunho sem regra explícita.

## API

Prefixo `/api/v1/forms/`:

- lista/criação e detalhe;
- `duplicate/`, `archive/`, `restore/`;
- submissões por formulário;
- templates e detalhe;
- criação a partir de template;
- detalhe e `submit/` de submissão.

## Frontend

Rota `/dashboard/formularios` contém construtor e gestão. Validação cliente melhora usabilidade, mas o backend deve validar tipo e obrigatoriedade.

## Permissões e segurança

Owner limita o escopo. Respostas podem conter dados sensíveis e devem ser tratadas conforme o contexto clínico. JSON não deve aceitar HTML executável. Exportações precisam de autorização e auditoria.

## Limitações

- política de imutabilidade/revisão após submissão precisa permanecer consistente em todos os endpoints;
- não há portal público de paciente documentado como completo;
- retenção depende da política institucional;
- templates globais exigem governança administrativa.

[Voltar aos módulos](../README.md)
