# Roadmap de implementação — Elo Terapêutico

## Estado atual verificado

| Área | Implementação encontrada | Maturidade | Observação principal |
| --- | --- | --- | --- |
| Usuários e autenticação | `apps/users`, Simple JWT, rotação, blacklist, lockout, reset e BFF Next.js | Implementada, em validação de estabilização | Access/refresh ficam em cookies HttpOnly; esta revisão adiciona sanitização, CSRF e E2E. |
| Pacientes | `apps/patients`, services, selectors, importação e lifecycle | Com dívida técnica | Isolamento predominante por terapeuta, sem tenant explícito. |
| Prontuário | `apps/records`, evoluções, anamnese, anexos e exportações | Parcial | Exige tenant explícito, optimistic locking, retenção e pipeline antimalware. |
| Agenda | `apps/scheduling` (`label=agenda`), services, recorrências, salas, pacotes e locks | Parcial | Revisar calendário mensal, timezone e concorrência PostgreSQL. |
| Telemedicina | Sala lógica, tokens, expiração e acesso público | Parcial | Não existe infraestrutura de áudio e vídeo em tempo real. |
| Financeiro clínico | `apps/finances` (`label=financeiro`), services, selectors e relatórios | Parcial | Preservar separação em relação ao Billing e migrar ownership para tenant. |
| Documentos | `apps/documents`, models/services/selectors/views separados | Parcial/configurável | Ampliar versionamento, retenção, assinatura e storage privado operacional. |
| Formulários | `apps/forms`, templates, submissões e respostas | Parcial | Consolidar snapshots/versionamento e portal público seguro. |
| Comunicações | Domínio/aplicação/infra, Celery, retries e webhooks | Parcial/configurável | Provedores oficiais, DLQ, limites, quiet hours e observabilidade. |
| Relatórios | Selectors/services/views | Parcial | Necessita suíte própria, métricas documentadas e exportação assíncrona uniforme. |
| Billing | `apps/billing`, Asaas, planos, assinatura, entitlements e pagamentos | Parcial/configurável | Validar todos os estados em staging e reconciliar backlog histórico. |
| Auditoria | `apps/audit` refatorado, com sanitização, selectors, services e testes | Parcial | Refatoração integrada; ainda é necessário validar retenção e cobertura transversal. |
| Tenant/clínica | Inexistente | Incompleto | Bloqueador arquitetural para clínica, equipe e múltiplos profissionais. |
| Portal do paciente | Inexistente como domínio completo | Incompleto | Criar autenticação, permissões e fluxos próprios. |
| Inteligência artificial | Feature flag e placeholder | Planejada | Não há provedor nem fluxo funcional; deve permanecer assistiva e supervisionada. |

## Ordem de execução

1. **Estabilização, autenticação e CI** — em implementação na branch `agent/estabiliza-autenticacao-ci`:
   - respostas BFF sanitizadas;
   - cookies HttpOnly e double-submit CSRF validados;
   - E2E de login, refresh e logout;
   - PostgreSQL no CI;
   - Ruff e mypy como gates obrigatórios.
2. **Multi-tenancy e isolamento por clínica** — próximo bloqueador estrutural.
3. **Contratos OpenAPI/TypeScript, cobertura e E2E dos módulos principais**.
4. **Dashboard, onboarding, agendamento público e portal do paciente**.
5. **Telemedicina real com provedor de mídia abstraído**.
6. **IA administrativa e, posteriormente, assistência clínica supervisionada**.
7. **Administração, auditoria, LGPD, retenção e resposta a incidentes**.
8. **Produção, observabilidade, backup/restauração e runbooks**.

## Estratégia de migrations

- Não reescrever migrations históricas.
- Aplicar `expand → migrate/backfill → contract`.
- Separar alteração de schema, backfill e obrigatoriedade/constraints.
- Backfills devem ser idempotentes e executáveis em lotes.
- Não apagar registros incompatíveis; produzir relatório de inconsistências.

## Critérios de aceite por PR

- escopo restrito e arquitetura atual preservada;
- autorização aplicada no backend;
- migrations revisadas e não destrutivas;
- testes adicionados para sucesso, negação e regressão;
- validações backend/frontend executadas quando aplicáveis;
- OpenAPI e documentação atualizados quando o contrato mudar;
- nenhum dado clínico, segredo, token ou payload bruto em logs/diff;
- riscos e limitações documentados;
- workflows obrigatórios aprovados antes do merge.

Consulte a [matriz de módulos](17-referencia/matriz-de-modulos.md) e a [auditoria do backlog](17-referencia/auditoria-backlog.md).
