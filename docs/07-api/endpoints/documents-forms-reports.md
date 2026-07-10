# Endpoints — Documentos, formulários e relatórios

## Documentos — `/api/v1/documents/`

- `templates/` — modelos privados;
- `library/` — biblioteca global e importação;
- `generated/` — documentos gerados, estados e download;
- `placeholders/` — catálogo seguro de placeholders.

Autenticação é exigida, exceto quando view declarar diferente. Owner e permissão de biblioteca controlam escopo.

## Formulários — `/api/v1/forms/`

- lista/criação e `{id}/`;
- `{id}/duplicate/`, `/archive/`, `/restore/`;
- `{form_id}/submissions/`;
- `templates/` e `templates/{id}/`;
- `from-template/{template_id}/`;
- `submissions/{id}/` e `/submit/`.

Respostas usam JSON, mas tipos e obrigatoriedade são definidos pelos campos.

## Relatórios — `/api/v1/reports/`

- `appointments/`;
- `patients/`;
- `financial/`;
- `online-scheduling/`;
- `export/`.

Filtros e formatos dependem da view. Toda consulta precisa respeitar o usuário autenticado e a confidencialidade dos domínios fonte.

[Voltar à API](../README.md)
