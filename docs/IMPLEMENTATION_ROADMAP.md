# Roadmap de implementação — Elo Terapêutico

## Estado atual verificado

| Área | Implementação encontrada | Maturidade | Observação principal |
| --- | --- | --- | --- |
| Usuários e autenticação | `apps/users`, Simple JWT, rotação, blacklist, lockout e reset | Parcial | access/refresh ainda são acessíveis ao JavaScript no frontend |
| Pacientes | `apps/patients`, services, selectors, importação e lifecycle | Com dívida técnica | isolamento predominante por terapeuta, sem tenant explícito |
| Prontuário | `apps/records`, evoluções, anamnese, anexos e exportações | Parcial | exige tenant explícito, optimistic locking e pipeline antivírus |
| Agenda | `apps/scheduling` (`label=agenda`), services, recorrências, salas, pacotes e locks | Parcial | revisar calendário mensal, timezone e concorrência PostgreSQL |
| Financeiro clínico | `apps/finances` (`label=financeiro`), services, selectors e relatórios | Parcial | preservar separação em relação ao Billing do SaaS |
| Documentos | `apps/documents`, models/services/selectors/views separados | Parcial | ampliar versionamento, fila, retenção e classificação de assinatura |
| Formulários | `apps/forms`, templates, submissões e respostas | Parcial | consolidar snapshots/versionamento e portal público seguro |
| Comunicações | domínio/aplicação/infra, fila persistente, retries e webhooks | Parcial | ampliar health, DLQ, limites, quiet hours e auditoria |
| Relatórios | selectors/services/views | Parcial | necessita suíte própria, métricas documentadas e exportação assíncrona |
| Billing | `apps/billing`, Asaas, planos, assinatura e pagamentos | Parcial | domínio separado das finanças clínicas |
| Tenant/clínica | inexistente | Incompleto | bloqueador arquitetural para clínica/equipe/múltiplos profissionais |

## Ordem de execução

1. Segurança crítica e autenticação.
2. Multi-tenancy e isolamento por clínica.
3. Contratos, testes e CI.
4. Dashboard e onboarding.
5. Evolução incremental dos módulos.
6. Administração, auditoria e LGPD.
7. Produção, observabilidade, backup e runbooks.

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
- riscos e limitações documentados.
