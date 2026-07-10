# Logs, auditoria e gestão de segredos

## Logging

Desenvolvimento usa console detalhado; produção configura JSON com structlog e nível INFO, reduzindo detalhes de `django.security` a ERROR.

### Não registrar

- Authorization, access/refresh tokens;
- senhas e tokens de reset;
- CPF/CNPJ completos;
- conteúdo de prontuário;
- documentos e respostas clínicas;
- chaves Asaas/Azure/SMTP;
- connection strings;
- dados de cartão, PIX copia e cola e QR code;
- payload bruto de webhook.

## Auditoria

`AuditLog` registra usuário, ação, IP, user agent, timestamp e objeto técnico. Model impede update/delete pela API ORM comum.

### Limitações

- administrador do banco ainda pode alterar dados;
- cobertura depende da instrumentação de cada endpoint;
- escrita é fail-open;
- retenção não está automatizada;
- auditoria não substitui logs de infraestrutura.

## Segredos

### Implementado

Produção rejeita valores ausentes, comuns ou menores que 32 caracteres e impede reutilização entre segredos principais.

### Operacional

- armazenar em Azure Key Vault ou secret manager equivalente;
- separar ambientes e contas;
- não colocar segredos em `NEXT_PUBLIC_*`;
- restringir leitura a identidades gerenciadas;
- rotacionar por calendário e incidente;
- invalidar credencial anterior;
- registrar quem alterou sem registrar o valor;
- escanear histórico Git e artefatos.

## Ferramentas

Workflow backend executa Bandit e pip-audit. GitHub secret scanning/GitGuardian dependem da configuração do repositório/serviço; não devem ser declarados ativos sem verificação externa.

[Voltar](README.md)
