# Matriz de integrações

A coluna **Status** distingue interface, implementação, configuração e validação operacional. Nenhuma integração externa deve ser apresentada como operacional somente pela presença de código.

| Serviço | Finalidade | Módulos consumidores | Dados envolvidos | Configuração | Status | Riscos e pendências |
| --- | --- | --- | --- | --- | --- | --- |
| Asaas | Checkout, cobrança, assinatura, webhooks e reconciliação | Billing SaaS | Identidade de cobrança, valores, status e IDs externos; sem dados clínicos | `ASAAS_API_KEY`, `ASAAS_BASE_URL`, `ASAAS_WEBHOOK_TOKEN` | 🟠 implementação presente; staging pendente | Credencial, URL de sandbox em produção, webhook falso, duplicidade, indisponibilidade e divergência de conciliação |
| LiveKit | Áudio e vídeo WebRTC, salas, tokens e webhooks | Agenda e Telemedicina | Mídia em trânsito e identificadores técnicos; dados clínicos não devem ir em identity/metadata | URL WSS, API key, API secret, webhook e parâmetros de E2EE | 🟠 implementação presente; desativada por padrão | HTTPS/WSS, E2EE, consumo, expiração, assinatura do webhook, contrato e smoke test em staging |
| Azure Blob Storage | Documentos, anexos e mídia privada | Prontuário, Documentos, Relatórios e exports | Arquivos clínicos e administrativos | Connection string, container, expiração e política de storage privado | 🟠 configurável; infraestrutura não comprovada | Container público, segredo, retenção, URLs longas, exclusão e restauração. O código auditado usa connection string; identidade gerenciada não está comprovada |
| SMTP/SendGrid | Recuperação de senha, convites e comunicações | Usuários, Organizações e Comunicações | E-mail, assunto, conteúdo administrativo e links temporários | Backend, host, porta, usuário, senha, TLS e remetente | 🟠 configurável; desenvolvimento usa console | Reputação, entrega, indisponibilidade, enumeração e token em logs |
| WhatsApp manual | Preencher mensagem e delegar envio ao aplicativo | Comunicações | Telefone e conteúdo administrativo mínimo | Não usa credencial de API; gera `wa.me` | ✅ implementado com confirmação humana | Abertura não comprova envio, entrega ou leitura; erro humano e exposição no dispositivo |
| WhatsApp Business | Canal oficial com templates e webhooks | Comunicações | Telefone, template e conteúdo administrativo permitido | Provider, base URL, token, phone number, verify token e app secret | 🟡 interface preparada; provider operacional não comprovado | Aprovação de template, consentimento, opt-out, assinatura, entrega e custo |
| SMS | Canal alternativo de lembrete | Comunicações | Telefone e mensagem administrativa curta | Provider, API key e sender | 🟡 interface preparada; provider não definido | Custo, consentimento, entrega, limite de caracteres e conteúdo sensível |
| PostgreSQL | Persistência, locks, constraints, auditoria e estados duráveis | Todos os domínios | Dados do sistema | `DATABASE_URL` e configuração do serviço | ✅ implementação principal | Acesso, backup, restauração, migração, locks, concorrência e disponibilidade |
| Redis | Broker, resultados temporários, cache e rate limit | Celery, backend e segurança | IDs técnicos, mensagens de task, chaves de cache; sem conteúdo clínico completo | `REDIS_URL`, `REDIS_RESULT_URL`, URLs Celery e senha | ✅ local / obrigatório em produção | Indisponibilidade, autenticação, persistência, rede, TTL e backlog |
| Celery | Exportações, uploads, comunicações, billing e manutenção | Records, Communications, Billing e Scheduling | IDs de jobs e payloads técnicos mínimos | Broker, result backend, quatro workers e Beat | ✅ implementação presente | Jobs presos, duplicidade, timeout, idempotência, observabilidade e dimensionamento |
| WeasyPrint | Geração de PDF | Records, Documents, Reports e Finances quando aplicável | Conteúdo renderizado no arquivo | Biblioteca Python e dependências Pango | ✅ implementado | SSRF, recursos externos, fontes, custo de CPU e falha nativa |
| OpenAPI/drf-spectacular | Contrato e documentação da API | Backend, frontend e integrações | Metadados de endpoints e schemas | Settings e comando `spectacular` | ✅ implementado | Divergência de contrato, exemplos sensíveis e exposição excessiva |
| GitHub Actions | CI, testes, segurança, imagens e documentação | Engenharia | Código, logs e dados sintéticos | Workflows e secrets do GitHub | ✅ implementado para validação | Artefatos com token/cookie, permissões excessivas, dependências de Actions e falsa impressão de deploy |
| Playwright | E2E de autenticação e gateway | Frontend/BFF | Usuários sintéticos, cookies de teste e respostas controladas | Pacote isolado, Chromium e workflow | ✅ implementado | Flakiness, artefatos sensíveis e dependência do ambiente completo |
| Django Admin/Unfold | Operação e suporte interno | Todos os apps registrados | Dados administrativos e clínicos conforme permissão | Superusuário, permissions e settings | ✅ implementado / ⚠️ operacional | Acesso privilegiado, least privilege, auditoria e exposição de dados |
| Provedor de IA | Assistência futura, resumos ou busca | Nenhum fluxo funcional atual | Potencialmente dados clínicos sensíveis | Não definida | 🔴 não implementado / 📌 planejado | Privacidade, isolamento, prompt injection, custos, alucinação e decisão clínica indevida |

## Fluxos de webhook

Webhooks externos devem:

1. validar autenticação ou assinatura;
2. evitar leitura integral desnecessária do payload em logs;
3. persistir evento e identificador externo;
4. aplicar idempotência;
5. responder rapidamente;
6. executar trabalho pesado de forma assíncrona;
7. registrar erro sanitizado;
8. permitir retry controlado e reconciliação.

## Dados clínicos

- gateways de pagamento não devem receber prontuário, diagnóstico, anamnese ou evolução;
- canais administrativos devem usar conteúdo mínimo;
- metadata de LiveKit deve conter identificadores opacos, não conteúdo clínico;
- logs e artefatos do CI usam somente dados sintéticos;
- storage clínico deve ser privado e ter política de retenção.

## Regras operacionais

1. nenhuma integração configurável deve ser apresentada como operacional sem teste em staging;
2. credenciais e payloads sensíveis não podem aparecer em logs, relatórios ou artefatos;
3. webhooks usam autenticação, idempotência, auditoria e retentativas;
4. LiveKit permanece desligado por padrão até configuração completa;
5. WhatsApp e SMS oficiais permanecem inativos sem provider completo;
6. falha externa deve produzir mensagem pública sanitizada;
7. cada integração deve ter timeout, métricas, alertas e runbook;
8. contratos com operadores e requisitos de privacidade precisam de avaliação própria.

[Voltar](README.md)
