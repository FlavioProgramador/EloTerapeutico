# Matriz de módulos

## Legenda

- ✅ **Implementado e validado:** fluxo principal existe e possui validação automatizada relevante;
- 🟡 **Implementado parcialmente:** existem camadas funcionais, mas faltam fluxos, cobertura ou regras importantes;
- 🟠 **Implementado, depende de integração/configuração:** código existe, porém operação depende de credenciais, provedor ou infraestrutura;
- 🔴 **Não implementado:** não existe fluxo funcional completo;
- ⚠️ **Não pronto para produção:** controles operacionais ou de segurança ainda impedem uso com dados reais;
- 📌 **Planejado:** intenção de produto sem implementação funcional comprovada.

| Módulo | Backend | Frontend | API | Assíncrono | Testes | Integrações | Tenant | Maturidade | Pendência principal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Core | Paginação, exceções, health checks, criptografia, quality gates e Admin dashboard | Componentes e infraestrutura compartilhada | Health e contratos transversais | Suporte a Celery e infraestrutura comum | Arquitetura, health e utilitários | PostgreSQL, Redis e storage | Base para enforcement | ✅ / 🟡 | Manter fronteiras arquiteturais e ampliar testes de integração. |
| Autenticação e usuários | `apps/users`, JWT, rotação, blacklist, lockout, reset e perfil | BFF Next.js, cookies HttpOnly, CSRF, providers e páginas de sessão | `/api/v1/auth/` | E-mail e fluxos auxiliares quando aplicável | Backend, unitários BFF e E2E | SMTP | Contexto é resolvido após autenticação | ✅ / ⚠️ | CSP, monitoramento, secrets e validação contínua em produção. |
| Organizações e multi-tenancy | `apps/organizations`, memberships, convites, settings e perfil profissional | Contexto, seletor, onboarding, organização e equipe | `/api/v1/organizations/` | Sem fila própria; contexto deve ser reconstruído por tasks consumidoras | Backend relevante; E2E parcial | E-mail para convites | Domínio central | 🟡 | Auditar ownership legado, tasks, relatórios, caches e integrações. |
| Pacientes | `apps/patients`, responsáveis, lifecycle, importação e exportação | `features/patients` e workspace | `/api/v1/patients/` | Importações/exportações conforme fluxo | Backend relevante | Nenhuma obrigatória | Parcialmente migrado | 🟡 | Garantir organização em todos os relacionamentos e ampliar E2E. |
| Prontuário | `apps/records`, anamnese, evoluções, metas, anexos, aditivos e exports | `features/records` | `/api/v1/records/` | Filas `exports` e `uploads` | Backend amplo | WeasyPrint e Azure Blob configurável | Deve usar organização e autoria | 🟡 / ⚠️ | Retenção, concorrência, storage privado e provider antimalware real. |
| Agenda e scheduling | Consultas, recorrências, bloqueios, salas, pacotes e telemedicina | Calendário, formulários, pacotes e atendimento online | `/api/v1/scheduling/` | Fila `default` para manutenção; integra Comunicações | Backend e testes de calendário | Comunicações e LiveKit | Contexto por organização | 🟡 | Validar timezone, recorrência mensal, concorrência e ownership. |
| Telemedicina | Salas, convites com hash, consentimento, E2EE, provider e webhooks | Lobby e chamada LiveKit para paciente e profissional | Dentro de `/api/v1/scheduling/` e rotas públicas controladas | Fila `default`; expiração periódica de salas | Backend e testes estruturais frontend | LiveKit e Comunicações | Tenant explícito | 🟠 / ⚠️ | Credenciais, HTTPS/WSS, webhook e smoke test em staging. |
| Financeiro clínico | `apps/finances`, receitas, despesas, pagamentos e relatórios | `features/financeiro` | `/api/v1/finances/` | Sem fila obrigatória para lançamentos internos | Backend relevante | Nenhuma obrigatória | Parcialmente migrado | 🟡 | Validar transições, conciliação e isolamento por organização. |
| Documentos | Templates, biblioteca, geração, hash e sequências | Workspace de documentos | `/api/v1/documents/` | Pode usar exports/uploads conforme tipo de arquivo | Backend relevante | WeasyPrint e Azure Blob | Deve usar organização | 🟠 / ⚠️ | Storage privado, retenção, versionamento e assinatura eletrônica. |
| Formulários | Templates, submissões e respostas | Construtor e integração com prontuário | `/api/v1/forms/` | Comunicações para lembretes | Parcial | Links públicos e Comunicações | Parcialmente migrado | 🟡 | Snapshot de versão, portal seguro e testes completos. |
| Comunicações | Comunicações, recipients, tentativas, templates, automações, preferências e notificações | Dashboard, histórico, templates, automações, canais e notificações | `/api/v1/communications/` e `/api/v1/public/communications/` | Fila `communications` e tarefas periódicas | Backend amplo e testes frontend específicos | SMTP, WhatsApp manual, WhatsApp Business e SMS | Deve respeitar organização e preferências | 🟠 | Providers oficiais, observabilidade, limites, quiet hours e validação em staging. |
| Relatórios | Selectors, services, agregações e exports | Dashboard de relatórios | `/api/v1/reports/` | Exportação quando aplicável | Parcial | PDF/storage | Migração em andamento | 🟡 | Métricas documentadas, testes por tenant e exportação uniforme. |
| Billing SaaS | Planos, preços, checkout, assinaturas, pagamentos, entitlements e webhooks | Pricing, checkout, assinatura e páginas de status | `/api/v1/billing/` | Fila `default`, webhooks e reconciliação periódica | Backend relevante e workflow dedicado | Asaas | Contratação associada à organização/owner | 🟠 | Credenciais, webhook autenticado, reconciliação e todos os estados. |
| Auditoria | `apps/audit`, contexto de request, sanitização e eventos | Django Admin | Interna quando exposta | Pode receber eventos de tasks e integrações | Backend ampliado | Nenhuma | Deve incluir tenant sem conteúdo sensível | 🟡 | Retenção, cobertura transversal e ações fora da ORM. |
| Administração | Django Admin e Django Unfold | Backoffice server-rendered | Não aplicável | Visualiza estados de jobs e integrações | Parcial | Nenhuma | Escopo operacional precisa ser revisto | ✅ / ⚠️ | Permissões, least privilege e procedimentos de suporte. |
| Dashboard | Endpoints agregadores por domínio | Dashboard Next.js | Endpoints de cada domínio | Não possui fila própria | Parcial | Nenhuma | Deve agregar somente tenant ativo | 🟡 | E2E, estados vazios/erro e métricas consolidadas. |
| Configurações | Settings de usuário, organização, atendimento e integrações | Páginas de configuração | Distribuída entre users, organizations e módulos | Sem fila própria | Parcial | Providers configuráveis | Organização ativa | 🟡 | Centralizar contratos e diferenciar configuração de operação validada. |
| Landing page | Sem domínio próprio relevante | `features/landing` e rota pública | Consome catálogo de planos quando aplicável | Não | Estrutural/parcial | Billing | Sem dados clínicos | ✅ | Manter conteúdo alinhado às features realmente disponíveis. |
| Onboarding | Estado em `Organization` e services do domínio | `/onboarding` | Organizações | Não | Backend relevante; E2E parcial | Nenhuma obrigatória | Organização criada | 🟡 | Cobrir retomada, troca de tenant e falhas intermediárias. |
| Checkout | Services e API de billing | `/checkout` e resultados | Billing público/autenticado conforme fluxo | Webhooks e reconciliação em `default` | Backend e testes frontend | Asaas | Contratação da organização | 🟠 | Staging, idempotência ponta a ponta e falhas do gateway. |
| Agendamento público | Estruturas e fluxos pontuais | Páginas públicas parciais | Parcial | Comunicações quando aplicável | Parcial | CAPTCHA/comunicação/pagamento ainda não comprovados | Tenant precisa ser resolvido com segurança | 🟡 | Reserva completa, confirmação, cancelamento, abuso e concorrência. |
| Portal do paciente | Não há domínio autenticado completo dedicado | Não há portal completo separado | Não | Não | Não | Comunicações/documentos | Não definido como portal | 🔴 | Criar autenticação, permissions, tenant e experiência exclusiva. |
| Inteligência artificial | Flag comercial e placeholders | Indicadores de indisponibilidade | Sem integração funcional | Não | Não | Provedor não definido | Governança ainda não definida | 🔴 / 📌 / ⚠️ | Consentimento, isolamento, auditoria, segurança e revisão humana. |

## Observações

1. A presença de model, tela, task ou endpoint isolado não torna um módulo pronto para produção.
2. Organizações e memberships existem; o risco atual é ownership legado incompleto, não ausência de tenant explícito.
3. A telemedicina possui mídia em tempo real no código, mas depende de LiveKit, HTTPS/WSS, webhook e staging.
4. A fila `uploads` implementa pipeline de verificação, mas não comprova provider antimalware externo ativo.
5. Billing SaaS e financeiro clínico são domínios distintos.
6. IA permanece planejada e não possui provedor ou fluxo funcional.
7. Integrações externas devem ser validadas em staging com credenciais próprias antes do uso real.

Consulte também a [Matriz de integrações](matriz-de-integracoes.md), a [Matriz de containers](matriz-de-containers.md), as [Limitações](../01-visao-geral/limitacoes.md) e a [Auditoria do backlog](auditoria-backlog.md).
