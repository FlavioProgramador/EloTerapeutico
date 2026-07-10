# Roadmap técnico recomendado

Este roadmap organiza pendências observadas; não representa compromisso de prazo.

## Prioridade 0 — Bloqueadores para dados reais

- definir arquitetura de tenant/clínica ou declarar formalmente operação individual;
- migrar autenticação para cookies seguros definidos pelo servidor ou outro mecanismo resistente a XSS;
- tornar storage privado persistente obrigatório em produção;
- implantar backup, restauração testada, monitoramento e alertas;
- definir política de retenção, exclusão e resposta a incidentes;
- revisar permissões de todos os papéis e recursos clínicos;
- configurar segredos em secret manager e validar webhook Asaas.

## Prioridade 1 — Qualidade e operação

- ampliar testes frontend e end-to-end;
- reduzir módulos ignorados pelo `mypy`;
- adicionar verificação automática de links da documentação;
- automatizar smoke tests pós-deploy;
- documentar SLOs, alertas e runbooks do ambiente escolhido;
- testar rotação de chave de criptografia e restauração de backup.

## Prioridade 2 — Evolução do produto

- formalizar gestão de clínica/equipe;
- consolidar o prefixo de billing;
- tornar notificações e e-mails assíncronos;
- adicionar análise antimalware aos uploads;
- criar política de versionamento e depreciação da API;
- evoluir telemedicina conforme requisitos técnicos e regulatórios.

## Regra de atualização

Toda funcionalidade nova deve atualizar, no mesmo Pull Request:

- documentação do módulo;
- caso de uso;
- endpoint e payload, quando aplicável;
- controles e riscos de segurança;
- testes e migrations.

[Voltar](README.md)
