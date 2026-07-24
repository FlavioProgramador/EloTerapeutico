# 05 — Módulos

Cada página reúne finalidade, situação, entidades, regras, API, interface, permissões, segurança, testes, integrações e limitações. A presença de um model, tela ou endpoint isolado não classifica um módulo como concluído.

## Legenda

- ✅ implementado e validado;
- 🟡 implementado parcialmente;
- 🟠 implementado, dependente de integração ou configuração;
- 🔴 não implementado;
- ⚠️ não pronto para produção;
- 📌 planejado.

## Domínios

| Módulo | Documento | Situação |
| --- | --- | --- |
| Autenticação | [autenticacao](autenticacao/README.md) | ✅ com validação contínua de segurança |
| Usuários | [usuarios](usuarios/README.md) | ✅ |
| Organizações e multi-tenancy | [organizacoes](organizacoes/README.md) | 🟡 ownership legado em migração |
| Dashboard | [dashboard](dashboard/README.md) | 🟡 |
| Pacientes | [pacientes](pacientes/README.md) | 🟡 |
| Prontuário | [prontuario](prontuario/README.md) | 🟡 / ⚠️ dados clínicos |
| Agenda | [agenda](agenda/README.md) | 🟡 |
| Telemedicina | [telemedicina](telemedicina/README.md) | 🟠 / ⚠️ LiveKit, HTTPS/WSS e staging |
| Financeiro clínico | [financeiro](financeiro/README.md) | 🟡 |
| Documentos | [documentos](documentos/README.md) | 🟠 / ⚠️ storage privado |
| Formulários | [formularios](formularios/README.md) | 🟡 |
| Comunicações | [comunicacoes](comunicacoes/README.md) | 🟠 provedores externos |
| Relatórios | [relatorios](relatorios/README.md) | 🟡 |
| Billing/assinatura | [billing](billing/README.md) | 🟠 Asaas e webhooks |
| Auditoria | [auditoria](auditoria/README.md) | 🟡 |
| Administração | [administracao](administracao/README.md) | ✅ com revisão operacional pendente |
| Configurações | [configuracoes](configuracoes.md) | 🟡 |
| Notificações | [notificacoes](notificacoes.md) | ✅ dentro de Comunicações |

## Superfícies de produto

| Superfície | Situação | Referência |
| --- | --- | --- |
| Landing page | ✅ interface pública implementada | `frontend/src/features/landing/` |
| Onboarding | 🟡 fluxo persistido por organização | [Organizações](organizacoes/README.md) |
| Checkout | 🟠 depende de Asaas | [Billing](billing/README.md) |
| Agendamento público | 🟡 fluxos pontuais; reserva pública completa ainda pendente | [Agenda](agenda/README.md) |
| Portal do paciente | 🔴 não existe domínio autenticado completo e separado | [Matriz de módulos](../17-referencia/matriz-de-modulos.md) |
| Inteligência artificial | 📌 planejada, sem provedor ou fluxo funcional | [Matriz de integrações](../17-referencia/matriz-de-integracoes.md) |

## Observações

- Organizações, memberships e contexto de tenant existem no código atual; documentos históricos que indiquem ausência de tenant representam estados anteriores.
- A telemedicina possui mídia em tempo real com LiveKit no código, mas permanece indisponível até configuração, HTTPS/WSS, webhook e validação em staging.
- Comunicações usa Celery na fila `communications`; comandos de management legados não representam os containers atuais.
- Billing SaaS e financeiro clínico são domínios diferentes: um controla acesso comercial ao produto, o outro registra operações financeiras da prática clínica.
- Integrações externas não devem ser apresentadas como operacionais sem credenciais e teste em staging.

[Voltar ao índice](../README.md)
