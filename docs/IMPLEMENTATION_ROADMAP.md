# Roadmap de implementação — Elo Terapêutico

## Contexto da auditoria

- **Commit-base:** `2f331baf85387e8a2d8ed4df7cc8c47d98d7ea15` (`main`, 15/07/2026).
- **Objetivo:** evoluir o produto de forma incremental, sem reescrever a arquitetura funcional, sem alterar produção e sem criar uma segunda camada genérica `core`.
- **Regra de entrega:** cada risco é tratado em branch e Pull Request pequenos, com testes, documentação, migrations revisadas e rollback descrito.
- **Dados:** não utilizar dados reais de pacientes em código, testes, evidências ou logs.

## Estado atual verificado

### Backend

| Área | Implementação encontrada | Maturidade | Observação principal |
| --- | --- | --- | --- |
| Usuários e autenticação | `apps/users`, Simple JWT, rotação, blacklist, lockout e reset | Parcial | access/refresh ainda são acessíveis ao JavaScript no frontend |
| Pacientes | `apps/patients`, services, selectors, importação e lifecycle | Com dívida técnica | isolamento predominante por terapeuta, sem tenant explícito |
| Prontuário | `apps/records`, evoluções, anamnese, anexos e exportações | Parcial | exige tenant explícito, optimistic locking e pipeline antivírus |
| Agenda | `apps/scheduling` (`label=agenda`), services, recorrências, salas, pacotes e locks | Parcial | revisar calendário mensal, timezone e concorrência PostgreSQL |
| Financeiro clínico | `apps/financeiro`, services, selectors e relatórios | Parcial | preservar separação em relação ao Billing do SaaS |
| Documentos | `apps/documents`, models/services/selectors/views separados | Parcial | ampliar versionamento, fila, retenção e classificação de assinatura |
| Formulários | `apps/forms`, templates, submissões e respostas | Parcial | consolidar snapshots/versionamento e portal público seguro |
| Comunicações | domínio/aplicação/infra, fila persistente, retries e webhooks | Parcial | ampliar health, DLQ, limites, quiet hours e auditoria |
| Relatórios | selectors/services/views | Parcial | necessita suíte própria, métricas documentadas e exportação assíncrona |
| Billing | `apps/billing`, Asaas, planos, assinatura e pagamentos | Parcial | há rota duplicada `/api/billing/`; manter `/api/v1/billing/` canônica |
| Auditoria | `apps/audit`, minimização parcial e imutabilidade por instância | Com dívida técnica | `QuerySet.update/delete` e proteção append-only ainda precisam revisão |
| Administração | Django Admin + Unfold | Parcial | SQL Explorer é risco P0; dashboard operacional ainda incompleto |
| Tenant/clínica | inexistente | Incompleto | bloqueador arquitetural para clínica/equipe/múltiplos profissionais |

### Frontend

- Next.js App Router, React, TypeScript, Tailwind e TanStack Query.
- Organização majoritariamente por `features/`.
- Dashboard agrega vários endpoints e pode falhar de forma ampla.
- Testes automatizados não cobrem toda a interface.
- Sessão JWT atual requer migração para BFF/cookies `HttpOnly`.
- Estados de loading, erro, vazio, plano e permissão devem ser padronizados.

### Infraestrutura e qualidade

- PostgreSQL, Redis, Celery, Azure Blob e Gunicorn estão previstos/configuráveis.
- Produção já exige segredos fortes e storage privado quando configurado.
- CI e documentação existem, mas precisam consolidar testes frontend, PostgreSQL, segurança, SBOM e scans.
- Backup, restauração, observabilidade e resposta a incidentes ainda dependem de runbooks e validação operacional.

## Achados priorizados

| ID | Prioridade | Área | Problema | Solução incremental | Dependências | PR planejado |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-001 | P0 | Admin | SQL bruto é executado com validação pela primeira palavra, exceções são expostas e queries ficam no navegador | feature flag desligada por padrão, proibição em produção, permissão explícita, parser estrutural, transação read-only, timeout, allowlist, limite e auditoria por hash | nenhuma | `security/harden-admin-sql` |
| SEC-002 | P0 | Auth | tokens acessíveis ao JavaScript ampliam impacto de XSS | BFF Next.js, cookies `HttpOnly`, CSRF, refresh coordenado, revogação e sessões | SEC-001 independente | `security/http-only-auth` |
| SEC-003 | P0 | Upload clínico | arquivos não passam por antivírus | quarentena, validação, scanner abstrato/ClamAV, liberação e cleanup | workers/infra | `security/clinical-upload-scanning` |
| TEN-001 | P0 | Tenant | não existe entidade explícita de clínica | `Clinic`, memberships, convites, roles, clínica ativa e backfill expand/migrate/contract | SEC-002 | `feat/clinic-multitenancy` |
| TEN-002 | P0 | Isolamento | recursos são filtrados principalmente por usuário | tenant obrigatório em models/selectors/services/permissions e testes cruzados | TEN-001 | PRs por módulo |
| API-001 | P1 | Billing | `/api/v1/billing/` e `/api/billing/` coexistem | rota canônica, headers de depreciação, migração de consumidores e remoção posterior | inventário de consumidores | `refactor/billing-canonical-route` |
| API-002 | P1 | Contratos | OpenAPI, TypeScript, Zod e services podem divergir | geração/checagem automática e contratos por operação | TEN-001 | `refactor/api-contracts` |
| DASH-001 | P1 | Dashboard | múltiplos endpoints e falha global | endpoint agregado por blocos, resposta parcial, cache privado e onboarding real | TEN-001/API-002 | `feat/dashboard-aggregation` |
| AUD-001 | P1 | Auditoria | imutabilidade não cobre operações em massa/banco | manager append-only, proteção PostgreSQL, request ID e alertas | TEN-001 | `security/audit-append-only` |
| LGPD-001 | P1 | Dados | retenção, exportação e exclusão não formam política global | services explícitos, consentimento versionado e tarefas de limpeza | TEN-001/AUD-001 | `feat/lgpd-data-lifecycle` |
| TEST-001 | P1 | Testes | frontend e concorrência PostgreSQL não estão plenamente cobertos | Vitest/RTL/MSW/Playwright/axe e job PostgreSQL | API-002 | `test/frontend-test-suite` |
| OPS-001 | P2 | Produção | deploy/rollback/restore/segredos/workers sem runbooks completos | documentação operacional Azure e health/readiness/liveness | fases anteriores | `infra/production-observability` |
| UX-001 | P2 | Frontend | estados, acessibilidade e padrões visuais variam por módulo | design system, WCAG 2.2 AA e testes axe | TEST-001 | PRs por feature |
| PERF-001 | P2 | Desempenho | otimizações não estão centralmente medidas | baseline de consultas, bundle e Web Vitals antes/depois | TEST-001 | PRs por módulo |
| AI-001 | P3 | IA | recursos futuros podem tocar dados clínicos | opt-in, revisão humana, base legal e proibição de decisão autônoma | LGPD-001 | futuro |

## Issues e Pull Requests relacionados

Nenhuma issue nova deve ser criada para executar este roadmap. Itens existentes devem ser reaproveitados quando correspondentes.

- Issues abertas relevantes: `#31` contratos TypeScript, `#33` auditoria, `#34` testes, `#35` recorrência/timezone, `#36` documentação, `#37` integridade, `#38` exportações, `#115`–`#123` Billing e planos, `#157`/`#158` organização do core.
- Pull Requests abertos observados no commit-base: `#159` exceções/handler DRF e `#155` organização do app Documentos.
- Antes de fechar qualquer issue, validar código, migrations e testes no commit integrado.

## Ordem de execução

1. **Fase 0 — diagnóstico e preparação:** este roadmap, inventário, dependências e rollback.
2. **Fase 1 — segurança crítica:** SQL Explorer, autenticação `HttpOnly`, rota Billing e uploads clínicos.
3. **Fase 2 — multi-tenancy:** entidades, backfill, clínica ativa, permissões e isolamento por módulo.
4. **Fase 3 — contratos, testes e CI:** OpenAPI/TypeScript, frontend tests, E2E e PostgreSQL no CI.
5. **Fase 4 — Dashboard e onboarding:** endpoint agregado, blocos resilientes e progresso persistido.
6. **Fase 5 — módulos:** pacientes, prontuário, agenda, financeiro, documentos, formulários, comunicações, relatórios e Billing em PRs separados.
7. **Fase 6 — administração e auditoria:** Unfold operacional, ações seguras e append-only.
8. **Fase 7 — LGPD:** consentimentos, retenção, exportação, anonimização e exclusão controlada.
9. **Fase 8 — produção:** Azure, observabilidade, backup/restore e runbooks.
10. **Fase 9 — UX:** design system, WCAG 2.2 AA e desempenho medido.

## Estratégia de migrations

- Não reescrever migrations históricas.
- Aplicar `expand → migrate/backfill → contract`.
- Separar alteração de schema, backfill e obrigatoriedade/constraints.
- Backfills devem ser idempotentes e executáveis em lotes.
- Validar órfãos antes de adicionar `NOT NULL` ou unicidade por clínica.
- Não apagar registros incompatíveis; produzir relatório de inconsistências.
- Testar upgrade e rollback técnico quando a operação for reversível.

## Critérios de aceite por PR

- escopo restrito e arquitetura atual preservada;
- autorização aplicada no backend;
- migrations revisadas e não destrutivas;
- testes adicionados para sucesso, negação e regressão;
- `ruff`, formatter, mypy, `manage.py check`, migration check e pytest executados quando aplicáveis;
- lint, typecheck, testes e build frontend executados quando aplicáveis;
- OpenAPI/documentação atualizados quando o contrato mudar;
- nenhum dado clínico, segredo, token ou payload bruto em logs/diff;
- riscos e limitações documentados;
- rollback seguro descrito no Pull Request.

## Estratégia de rollback

- Reverter o commit/PR da fase quando não houver migration de dados.
- Para migrations `expand`, manter campos/tabelas adicionais até confirmar que consumidores antigos não dependem deles.
- Nunca fazer rollback destrutivo automático de backfill clínico.
- Feature flags devem permitir desativar integrações novas sem remover dados.
- Em autenticação, manter janela de compatibilidade curta e observável para sessões antigas antes da remoção definitiva.
- Em tenant, preservar o vínculo legado durante a transição até a validação completa de órfãos e testes cruzados.

## Riscos externos

- configuração de usuário de banco read-only para ferramentas administrativas;
- ClamAV ou serviço equivalente disponível nos ambientes autorizados;
- configuração de cookies/domínios/HTTPS no frontend e backend;
- credenciais Asaas, e-mail, Redis, Azure Blob e Key Vault;
- branch protection e permissões mínimas dos workflows;
- validação de backup por restauração em ambiente autorizado.
