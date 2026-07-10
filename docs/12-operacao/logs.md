# Logs e monitoramento

## Sinais essenciais

### API

- taxa/latência por rota e status;
- 401, 403, 429, 500 e 502;
- falha de auditoria;
- falha de storage;
- conexões/bloqueios do banco;
- reset de senha sem expor e-mail;
- erros Asaas por operação.

### Worker

- jobs por status;
- idade do job mais antigo;
- duração de processamento;
- retries e jobs presos;
- falhas de PDF/storage;
- ausência de heartbeat.

### Frontend

- erros de build/runtime;
- falhas de API e refresh;
- Web Vitals;
- erro de navegação/checkout;
- release/SHA.

### Infraestrutura

CPU, memória, disco, conexões, cache, storage, egress, certificados e backup.

## Alertas sugeridos

- health degradado;
- 5xx acima do baseline;
- fila pendente crescendo;
- webhook falhando/repetindo;
- storage negando escrita;
- backup falhou;
- login anômalo/429 elevado;
- secret/certificado próximo de expirar.

## Privacidade

Use IDs técnicos, correlação e tipo de erro. Não envie corpo de requests clínicos para APM.

[Voltar](README.md)
