# Matriz de módulos

## Legenda

- ✅ **Implementado e validado:** fluxo principal existe e possui validação automatizada relevante.
- 🟡 **Implementado parcialmente:** existem camadas funcionais, mas faltam fluxos, cobertura ou regras importantes.
- 🟠 **Implementado, mas depende de integração/configuração:** o código existe, porém a operação depende de credenciais, provedor ou infraestrutura.
- 🔴 **Não implementado:** não existe fluxo funcional completo.
- ⚠️ **Não pronto para produção:** controles operacionais ou de segurança ainda impedem uso com dados reais.

| Módulo | Backend | Frontend | API | Testes | Integração externa | Maturidade | Pendência principal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Autenticação e usuários | `apps/users`, JWT, rotação, blacklist, lockout e reset | BFF Next.js com cookies HttpOnly e double-submit CSRF | Sim | Backend, unitários BFF e E2E | SMTP para recuperação | ✅ Implementado e validado | Validar os workflows desta revisão no PR e manter CSP/monitoramento em produção. |
| Organizações/multi-tenancy | Não há entidade explícita de clínica/organização | Não há gestão de equipes por clínica | Não | Não | Não | 🔴 Não implementado / ⚠️ | Isolamento predominante por terapeuta; bloqueador para clínicas e múltiplos profissionais. |
| Pacientes | `apps/patients`, responsáveis, lifecycle, importação/exportação | `features/patients` | Sim | Backend relevante | Não | 🟡 Implementado parcialmente | Migrar ownership de terapeuta para tenant explícito e ampliar E2E. |
| Prontuário | `apps/records`, anamnese, evoluções, metas, anexos e exportações | `features/records` | Sim | Backend amplo | Azure Blob configurável; antivírus ausente | 🟡 Implementado parcialmente / ⚠️ | Tenant explícito, política de retenção, optimistic locking e pipeline antimalware. |
| Agenda | `apps/scheduling`, consultas, recorrências, bloqueios, salas e pacotes | `features/agenda` | `/api/v1/scheduling/` | Backend e calendário frontend | Comunicações para lembretes | 🟡 Implementado parcialmente | Validar timezone, recorrência mensal e concorrência em PostgreSQL. |
| Telemedicina | Tokens, sala lógica, expiração e controle de acesso | Tela pública de acesso | Sim | Testes de acesso/sala | Provedor de áudio e vídeo não configurado | 🟡 Implementado parcialmente / ⚠️ | Não há infraestrutura WebRTC/SFU nem chamada de áudio e vídeo funcional. |
| Financeiro clínico | `apps/finances`, receitas, despesas, pagamentos e relatórios | `features/financeiro` | `/api/v1/finances/` | Backend relevante | Gateway não é necessário para lançamentos internos | 🟡 Implementado parcialmente | Validar ownership por tenant, transições e conciliação ponta a ponta. |
| Documentos | Templates, biblioteca, geração e hash | Feature de documentos | Sim | Backend relevante | Azure Blob configurável; WeasyPrint | 🟠 Depende de integração/configuração / ⚠️ | Storage privado obrigatório, retenção, versionamento e assinatura eletrônica. |
| Formulários | Templates, submissões e respostas | Construtor e consumo no prontuário | Sim | Parcial | Link/portal público | 🟡 Implementado parcialmente | Versionamento por snapshot, portal seguro e testes completos. |
| Comunicações | Fila persistente, templates, automações, tentativas e notificações | Dashboard/configurações | Sim | Backend amplo | SMTP, WhatsApp e SMS configuráveis | 🟠 Depende de integração/configuração | Provedores oficiais, DLQ, quiet hours, limites e observabilidade operacional. |
| Relatórios | Selectors, services, exports e agregações | Dashboard de relatórios | Sim | Parcial | PDF/storage quando aplicável | 🟡 Implementado parcialmente | Cobertura própria, métricas documentadas e exportação assíncrona uniforme. |
| Billing do SaaS | Planos, preços, assinaturas, pagamentos, entitlements e webhooks | Pricing, checkout e assinatura | `/api/v1/billing/` | Backend relevante | Asaas | 🟠 Depende de integração/configuração | Credenciais reais, webhook autenticado, reconciliação e testes de todos os estados. |
| Auditoria | `apps/audit` refatorado, com trilha e sanitização de eventos | Django Admin | Sim, quando exposto internamente | Backend ampliado | Não | 🟡 Implementado parcialmente | Revalidar retenção, cobertura transversal e proteção fora da camada ORM. |
| Administração | Django Admin e Unfold | Backoffice server-rendered | Não aplicável | Parcial | Não | ✅ Implementado e validado | Revisar permissões operacionais antes da produção. |
| Dashboard | Endpoints agregadores por domínio | Dashboard Next.js | Sim | Parcial | Não | 🟡 Implementado parcialmente | E2E, estados vazios/erro e métricas consolidadas por tenant. |
| Agendamento público | Estruturas e relatórios relacionados existem | Fluxos públicos pontuais | Parcial | Parcial | Comunicação/pagamento opcionais | 🟡 Implementado parcialmente | Concluir reserva pública, confirmação, cancelamento, CAPTCHA e concorrência. |
| Portal do paciente | Não há domínio completo dedicado | Não há portal completo separado | Não | Não | Comunicações/documentos | 🔴 Não implementado | Criar autenticação, permissões e experiência exclusiva do paciente. |
| Inteligência artificial | Flag de plano e placeholder de resumo | Indicador de indisponibilidade | Não há integração funcional | Não | Provedor de IA não configurado | 🔴 Não implementado / ⚠️ | Governança, consentimento, isolamento, auditoria e uso somente assistivo. |

## Observações

1. A presença de model, tela ou endpoint isolado não torna um módulo pronto para produção.
2. Telemedicina refere-se atualmente à sala lógica e ao controle de acesso, não à mídia em tempo real.
3. IA está planejada e condicionada por plano, mas não possui provedor ou fluxo clínico funcional.
4. As integrações externas devem ser validadas em staging com credenciais próprias antes do uso real.
5. Consulte também a [matriz de integrações](matriz-de-integracoes.md), as [limitações](../01-visao-geral/limitacoes.md) e a [auditoria do backlog](auditoria-backlog.md).
