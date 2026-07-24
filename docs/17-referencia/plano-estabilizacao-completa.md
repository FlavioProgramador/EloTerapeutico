# Plano de estabilização completa

## Referência

- **branch:** `agent/estabilizacao-completa-site`;
- **SHA inicial da `main`:** `be9116d6c9adc40f35d421761a3318aac179ae30`;
- **data do baseline:** 24/07/2026;
- **Pull Request:** draft #225;
- **deploy:** não realizado;
- **issues criadas:** nenhuma.

## Evidências do baseline

| Gate | Resultado inicial | Evidência operacional |
| --- | --- | --- |
| Django CI | sucesso | PostgreSQL 15, migrations, Ruff, mypy e pytest |
| Frontend CI | sucesso com dívida | lint, typecheck, 79 testes no runner do CI, cobertura instrumentada e build |
| Dependency Security | sucesso | `pip-audit` e `npm audit` |
| Docker Images | sucesso | build das imagens existentes |
| CodeQL | sucesso | análise estática do GitHub |
| Cobertura backend | 67,61% de linhas | `coverage.xml` do baseline |
| ESLint frontend | 91 warnings | relatório do baseline |

Um workflow verde significa que o gate configurado passou. Não significa que todos os módulos estão completos ou prontos para dados reais.

## Plano por módulo

| Módulo | Backend/API | Frontend | Tenant e permissões | Assíncrono/integrações | Testes e segurança | Estado inicial | Objetivo desta estabilização |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core | health, exceções, criptografia e quality gates | infraestrutura compartilhada | base do enforcement | Redis, storage e Celery | arquitetura e health | ✅ / 🟡 | correlation ID, headers, contrato e gates de prontidão |
| Usuários | JWT, reset, lockout e perfil | BFF, cookies e sessão | tenant após autenticação | SMTP | unitários e E2E parcial | ✅ / ⚠️ | ampliar IDOR, headers, CSP e papéis administrativos |
| Organizações | organizations, memberships e convites | contexto, equipe e onboarding | domínio central | convites por comunicação | testes multi-tenant | 🟡 | executar auditoria de integridade no CI e ampliar cenários cruzados |
| Pacientes | CRUD, responsáveis, import/export | workspace e listagem | ownership parcialmente migrado | import/export | backend relevante | 🟡 | comprovar isolamento, deduplicação e rollback de importação |
| Prontuário | anamnese, evoluções, metas, anexos e exports | workspace clínico | tenant e autoria | filas `exports` e `uploads` | suíte ampla | 🟡 / ⚠️ | validar retenção, concorrência, scanner externo e links privados |
| Agenda | consultas, recorrências, bloqueios e pacotes | calendário e formulários | organização ativa | fila `default` e comunicações | testes de calendário | 🟡 | PostgreSQL concorrente, timezone e recorrência mensal |
| Telemedicina | salas, consentimento, E2EE e webhooks | lobby e chamada LiveKit | tenant explícito | LiveKit e comunicações | backend, estrutural e E2E | 🟠 / ⚠️ | smoke test condicional de staging e operação degradada |
| Financeiro clínico | receitas, despesas e pagamentos | dashboard financeiro | migração parcial | sem provider obrigatório | backend relevante | 🟡 | transições centralizadas, idempotência e conciliação |
| Documentos | templates, geração, hash e sequências | biblioteca e geração | tenant obrigatório | PDF e storage | backend relevante | 🟠 / ⚠️ | versionamento, retenção, storage e contrato OpenAPI |
| Formulários | templates, submissões e respostas | construtor | migração parcial | comunicações | cobertura parcial | 🟡 | snapshot imutável, tokens públicos e E2E |
| Comunicações | templates, tentativas e preferências | dashboard e notificações | tenant e opt-out | SMTP, WhatsApp e SMS | backend amplo | 🟠 | quiet hours, limites, provider oficial e observabilidade |
| Relatórios | selectors e agregações | dashboard | migração em andamento | exports | cobertura parcial | 🟡 | métricas exatas, tenant e consistência PDF/tela |
| Billing SaaS | planos, checkout, webhooks e entitlements | pricing e assinatura | organização/owner | Asaas e reconciliação | workflow dedicado | 🟠 | estados completos, replay e sandbox condicional |
| Auditoria | eventos sanitizados | Admin | organização sem conteúdo clínico | requests, tasks e integrações | suíte dedicada | 🟡 | correlation ID, retenção e cobertura fora da ORM |
| Administração | Unfold e SQL Explorer restrito | server-rendered | escopo operacional | visualização de jobs | cobertura parcial | ✅ / ⚠️ | least privilege, mascaramento e auditoria de ações |
| Portal do paciente | domínio incompleto | domínio incompleto | não consolidado | documentos/comunicações | ausente | 🔴 | implementar somente em bloco próprio com autenticação e E2E |
| Inteligência artificial | sem provider | placeholders/indisponibilidade | governança ausente | não aplicável | ausente | 🔴 / 📌 | remover promessa não entregue ou criar MVP assistivo revisável |

## Blocos de execução

1. **Fundação verificável:** documentação atual, correlation ID, headers defensivos, auditoria de tenant e contrato OpenAPI.
2. **Qualidade sem mascaramento:** registrar baseline, impedir regressão e reduzir warnings/ignores progressivamente.
3. **Isolamento transversal:** synthetic tests com duas organizações em cada domínio e workers.
4. **Fluxos críticos:** E2E de paciente, prontuário, agenda, financeiro, documentos, formulários e Billing.
5. **Operação:** storage privado, retenção, backup/restore, health degradado e observabilidade.
6. **Produto restante:** portal do paciente e decisão explícita sobre IA.

## Critério de conclusão

Uma linha da matriz somente pode ser promovida para ✅ quando houver fluxo funcional, permissão backend, tenant, estados de UI, testes relevantes, documentação e CI associados ao mesmo SHA. Integrações externas devem distinguir código, sandbox/staging e produção.

[Voltar](README.md)
