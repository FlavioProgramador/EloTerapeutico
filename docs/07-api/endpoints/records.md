# Endpoints — Prontuário

Base: `/api/v1/records/`.

## Paciente

- `patients/{patient_id}/anamnesis/`;
- `patients/{patient_id}/workspace/`;
- `patients/{patient_id}/clinical-anamnesis/`;
- `patients/{patient_id}/anamnesis-versions/`;
- `patients/{patient_id}/clinical-evolutions/`;
- `patients/{patient_id}/evolution-appointments/`;
- `patients/{patient_id}/goals/`;
- `patients/{patient_id}/documents/`;
- `patients/{patient_id}/forms/`;
- `patients/{patient_id}/exports/`;
- `patients/{patient_id}/export-pdf/`;
- `patients/{patient_id}/ai-summary/`.

## Evoluções

- `clinical-evolutions/{id}/`;
- `clinical-evolutions/{id}/finalize/`;
- `clinical-evolutions/{id}/duplicate/`;
- `clinical-evolutions/{id}/attachments/`;
- detalhe e download de anexo;
- router legado `evolutions/`.

## Outros recursos

- `clinical-templates/` e detalhe;
- `goals/{id}/`;
- `documents/{id}/` e `/download/`;
- `forms/{id}/`;
- `exports/{id}/retry/` e `/download/`.

## Regras comuns

JWT obrigatório; paciente precisa estar no escopo; conteúdo confidencial possui filtro adicional; downloads repetem autorização; uploads usam multipart e validação de assinatura; exportações criam jobs e dependem do worker.

## Exemplos de erro

- 400: data futura, conteúdo/arquivo inválido ou transição bloqueada;
- 403/404: sem acesso ao paciente ou confidencialidade;
- 409/400: evolução já vinculada ou estado incompatível, conforme view;
- 404/409: arquivo/job indisponível.

[Voltar à API](../README.md)
