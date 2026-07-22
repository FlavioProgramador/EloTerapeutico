# Matriz de integrações

| Integração | Uso | Configuração | Dados | Situação | Riscos e pendências |
| --- | --- | --- | --- | --- | --- |
| Asaas | Billing, cobrança, conciliação e webhook | API key, URL e token de webhook | Identidade de cobrança, valores e IDs externos | Implementado/configurável | Credenciais reais, idempotência, webhook falso e indisponibilidade; validar em staging. |
| Azure Blob | Arquivos clínicos e documentos privados | Connection string/container ou identidade gerenciada | Documentos e anexos | Parcial/configurável | Container público, perda de segredo, retenção e URLs temporárias; obrigatório em produção quando configurado. |
| SMTP/SendGrid | Reset de senha, comunicações e convites online | Host, porta, usuário e senha | E-mail e links temporários | Configurável | Entrega, reputação, indisponibilidade e vazamento de token em logs. |
| WhatsApp Business | Lembretes e comunicações operacionais | Provedor oficial, token, phone number e webhook | Telefone e conteúdo administrativo permitido | Parcial/configurável | Aprovação de templates, consentimento, opt-out, assinatura de webhook e confirmação de entrega. |
| SMS | Comunicações operacionais alternativas | Provedor, API key e remetente | Telefone e mensagem administrativa | Parcial/configurável | Custo, consentimento, entrega e exposição de conteúdo. |
| LiveKit | Áudio e vídeo WebRTC, salas, tokens e webhooks de telemedicina | URL WSS, API key, API secret e webhook | Mídia em trânsito e identificadores opacos | Implementado/configurável / ⚠️ | Exige HTTPS/WSS, E2EE, staging, monitoramento de consumo, validação de webhook e revisão contratual. Não recebe dados clínicos pela integração. |
| PostgreSQL | Persistência principal e testes de integração no CI | `DATABASE_URL` | Todos os domínios | Implementado | Acesso, backup, restauração, locks e concorrência. O workflow principal usa PostgreSQL 15. |
| Redis | Cache, rate limit, broker e resultados Celery | `REDIS_URL` e URLs do Celery | Chaves técnicas e estados de fila | Configurável/obrigatório em produção | Indisponibilidade, persistência, autenticação e rede. |
| Celery | Exportações, uploads, comunicações, billing e manutenção de telemedicina | Broker, result backend, workers e beat | IDs de jobs e payloads técnicos | Implementado/configurável | Jobs presos, duplicidade, observabilidade e dimensionamento dos workers. |
| WeasyPrint | Geração de PDF | Bibliotecas nativas | Conteúdo renderizado | Implementado | SSRF, falha nativa, fontes/recursos externos e custo de processamento. |
| OpenAPI | Documentação e contrato técnico da API | drf-spectacular | Metadados do contrato | Implementado | Exposição excessiva e divergência com tipos TypeScript. |
| IA clínica/administrativa | Resumos, assistência e busca semântica | Não definida | Potencialmente dados clínicos sensíveis | Não configurada/planejada | Privacidade, isolamento entre tenants, prompt injection, custos e decisão indevida. |
| Playwright | Validação E2E de autenticação | Pacote isolado e workflow GitHub Actions | Somente dados sintéticos | Implementado nesta revisão | Não armazenar cookies/tokens nos artefatos; execução depende do workflow passar. |

## Regras operacionais

1. Nenhuma integração configurável deve ser apresentada como operacional sem teste em staging.
2. Credenciais e payloads sensíveis não podem aparecer em logs, relatórios de teste ou artefatos do CI.
3. Webhooks devem utilizar autenticação, idempotência, auditoria e retentativas controladas.
4. A integração LiveKit permanece desativada por padrão até receber credenciais e validação operacional.

[Voltar](README.md)
