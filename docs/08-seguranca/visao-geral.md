# Visão geral de segurança

## Controles implementados

- Argon2 como hasher preferencial;
- validadores de senha do Django;
- JWT assinado por chave distinta, rotação e blacklist;
- invalidade de refresh após mudança de senha;
- anti-enumeração e dummy hashing;
- bloqueio temporário por tentativas falhas;
- rate limiting em endpoints de identidade no ambiente de produção;
- authorization classes, selectors e object permissions;
- criptografia Fernet em campos clínicos/documentais selecionados;
- confidencialidade por autor ou permissão explícita;
- sanitização de Markdown e validação de uploads por magic bytes;
- auditoria com representação mínima e imutabilidade no model;
- secrets fortes/distintos e sandbox Asaas proibido em produção;
- HTTPS redirect, HSTS, CORS explícito, anti-frame e nosniff;
- URLs temporárias no Azure Storage;
- redaction de payloads sensíveis de billing;
- Bandit, pip-audit e checks no workflow de segurança backend.

## Controles operacionais necessários

- secret manager e rotação;
- TLS e proxy confiável;
- PostgreSQL e Redis gerenciados;
- Azure Blob privado e persistente;
- IAM, rede e menor privilégio;
- backup e teste de restauração;
- observabilidade, alertas e retenção de logs;
- resposta a incidentes e comunicação;
- revisão de permissões e desligamento de usuários;
- política de retenção LGPD;
- antivírus/quarentena de uploads;
- proteção do Django Admin e SQL Explorer.

## Bloqueadores recomendados para produção clínica

1. remover tokens JWT de cookies acessíveis ao JavaScript;
2. definir formalmente isolamento por clínica ou limitar o produto a profissionais individuais;
3. exigir storage privado persistente;
4. implantar backup/restauração e monitoramento;
5. validar permissões por papel e conteúdo confidencial;
6. formalizar retenção, bases legais e atendimento ao titular;
7. configurar Asaas, SMTP, CORS, hosts e proxies com segredos fortes;
8. executar pentest e revisão de dependências no artefato de produção.

[Voltar](README.md)
