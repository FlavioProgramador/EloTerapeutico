# Dados tratados

| Categoria | Exemplos | Finalidade técnica | Local principal | Sensibilidade |
| --- | --- | --- | --- | --- |
| Identidade | nome, e-mail, role, registro profissional | conta e autorização | User | Pessoal |
| Autenticação | hash, falhas, bloqueio, tokens | controle de acesso | banco/token | Alta |
| Paciente | nome, CPF, nascimento, contato, endereço | cadastro e atendimento | Patient | Pessoal |
| Responsáveis | dados legal/financeiro/emergência | relação e cobrança | Patient | Pessoal |
| Clínicos | anamnese, evolução, CID, metas, anexos | cuidado e prontuário | records/storage | Sensível |
| Agenda | data, modalidade, notas, presença | organização de sessões | agenda | Pessoal/sensível por contexto |
| Financeiros | valores, status, vencimentos | gestão do profissional | financeiro | Pessoal/financeiro |
| Billing | plano, cobrança, IDs e URLs Asaas | assinatura do SaaS | billing/Asaas | Financeiro |
| Documentos | templates, PDFs, snapshots | emissão documental | documents/storage | Pode ser sensível |
| Formulários | campos, respostas, submissões | coleta estruturada | forms/records | Pode ser sensível |
| Auditoria | usuário, IP, user agent, objeto e ação | rastreabilidade | AuditLog | Pessoal/técnico |
| Infraestrutura | logs, métricas, IP, erros | operação e segurança | plataforma | Técnico/pessoal |

## Bases legais e finalidade

O código não implementa ou escolhe bases legais. A organização responsável deve documentar base, finalidade, compartilhamentos e prazo para cada categoria, especialmente dados de saúde.

## Compartilhamentos

Potenciais destinatários técnicos:

- provedor de nuvem/banco/storage;
- Asaas para billing;
- provedor SMTP;
- suporte autorizado;
- profissionais associados quando houver base e permissão.

Não use dados clínicos para treinamento de IA ou analytics sem avaliação específica, transparência e controles.

[Voltar](README.md)
