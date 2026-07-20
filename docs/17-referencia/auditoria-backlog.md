# Auditoria do backlog

## Referência

- data da auditoria: 20/07/2026;
- commit-base inicial: `807ddb96b79d2cb89ae84ca10cb615e1b969c1c1`;
- `main` observada ao final da revisão: `fafd3f661e96ba0635fd37c957ba9a840d7055fc`;
- branch de estabilização: `agent/estabiliza-autenticacao-ci`;
- issues abertas identificadas no início: 26;
- issues criadas por esta auditoria: 0;
- issues encerradas antes da validação do PR: 0.

Nenhuma issue foi encerrada apenas com base na existência de arquivos. Itens atendidos por esta branch permanecem abertos até que os workflows obrigatórios sejam executados e o PR seja revisado ou integrado. Durante o trabalho, a refatoração do app de auditoria foi integrada à `main`; a classificação abaixo já considera esse evento.

## Classificação

| Issue | Título resumido | Classificação | Justificativa e ação recomendada |
| ---: | --- | --- | --- |
| #26 | Multi-tenancy por clínica | PENDENTE VÁLIDA | Não existe entidade explícita de organização/clínica; permanece bloqueador arquitetural. |
| #27 | Sessão gerenciada pelo servidor | PARCIALMENTE CONCLUÍDA | O BFF já utilizava cookies HttpOnly. Esta branch elimina respostas de depuração e adiciona cobertura unitária/E2E para CSRF, refresh e logout. Encerrar somente após os workflows passarem e o PR ser integrado. |
| #28 | Imagem de produção | CONCLUÍDA, AGUARDANDO VALIDAÇÃO | O Dockerfile usa `requirements-prod.txt` por padrão e inicia `config.wsgi` com Gunicorn. Revalidar smoke test antes de encerrar. |
| #29 | Vínculo terapeuta/paciente em consultas | PENDENTE VÁLIDA | Depende do modelo de organização e das permissões de equipe. |
| #30 | Ownership e estados financeiros | PENDENTE VÁLIDA | O domínio financeiro foi refatorado, mas o aceite completo deve ser revalidado com equipe/clínica. |
| #31 | Contratos TypeScript/API | PENDENTE VÁLIDA | Ainda é necessário um gate automático de contrato OpenAPI ou geração de tipos. |
| #32 | Relações do prontuário | PENDENTE VÁLIDA | Existem validações e testes, mas o aceite integral deve ser revisto por entidade e tenant. |
| #33 | Auditoria e dados pessoais em logs | PARCIALMENTE CONCLUÍDA | A refatoração do app `audit` foi integrada à `main`. Revalidar retenção, cobertura transversal e critérios restantes antes de encerrar. |
| #34 | Cobertura dos módulos | PARCIALMENTE CONCLUÍDA | Backend possui suíte ampla; frontend ainda não cobre toda a interface. Esta branch acrescenta autenticação unitária e E2E. |
| #35 | Recorrência, timezone e concorrência | PENDENTE VÁLIDA | Requer validação específica em PostgreSQL e testes de calendário. |
| #36 | README e arquitetura | PARCIALMENTE CONCLUÍDA | Esta branch sincroniza status, autenticação e CI; documentação de outros domínios ainda deve ser revisada continuamente. |
| #37 | Integridade dos modelos | PENDENTE VÁLIDA | Há constraints em vários modelos, mas o escopo transversal ainda precisa de auditoria. |
| #38 | Exportações e recibos | PARCIALMENTE CONCLUÍDA | Exportações clínicas e geração de PDF existem; storage privado, recibos e operação devem ser validados ponta a ponta. |
| #39 | Manutenção de `core/fields.py` | SUBSTITUÍDA POR NOVA ESTRUTURA | O app `core` foi movido para `apps/core`; revisar o caminho canônico e encerrar como substituído somente após confirmar todos os critérios. |
| #79 | Startup local do backend | CONCLUÍDA, AGUARDANDO VALIDAÇÃO | Ambiente Docker e comandos de startup estão documentados. Manter aberta apenas se ainda houver reprodução do erro original. |
| #115 | Epic de planos e assinaturas | PARCIALMENTE CONCLUÍDA | Billing, planos, assinatura e Asaas existem; a epic deve ser reconciliada com os itens filhos antes do encerramento. |
| #116 | Models/admin/seed de billing | PARCIALMENTE CONCLUÍDA | Estruturas persistentes, admin e migrations existem. Revalidar checklist histórico. |
| #117 | API e services de assinatura | PARCIALMENTE CONCLUÍDA | API e services existem; confirmar todos os contratos previstos pela issue. |
| #118 | Features e limites por plano | PARCIALMENTE CONCLUÍDA | `has_feature`, entitlements e limites existem; falta comprovar aplicação uniforme. |
| #119 | Bloqueio por plano | PARCIALMENTE CONCLUÍDA | Há autenticação baseada em assinatura e feature flags, mas todos os módulos precisam de verificação. |
| #120 | Página de planos | PARCIALMENTE CONCLUÍDA | Frontend de pricing/checkout existe; confirmar que toda fonte de dados é canônica e não hardcoded. |
| #121 | Assinatura atual e upgrade | PARCIALMENTE CONCLUÍDA | Fluxo de billing existe; revisar todos os estados de upgrade, downgrade e bloqueio. |
| #122 | Testes de billing | PARCIALMENTE CONCLUÍDA | Existem testes de permissões, entitlements e checkout; comparar com o checklist completo. |
| #123 | Documentação de billing | PARCIALMENTE CONCLUÍDA | Há documentação específica do Asaas e endpoints; consolidar conteúdo duplicado antes de encerrar. |
| #157 | Hierarquia de exceções | BLOQUEADA/EM IMPLEMENTAÇÃO | Existe PR draft próprio. Esta branch não altera o escopo. |
| #158 | Organização do app core | BLOQUEADA/EM VALIDAÇÃO | A estrutura atual usa `apps/core`; reconciliar com PRs e issue antes de encerrar. |

## Totais da classificação

| Classificação | Quantidade |
| --- | ---: |
| PENDENTE VÁLIDA | 7 |
| PARCIALMENTE CONCLUÍDA | 14 |
| BLOQUEADA/EM IMPLEMENTAÇÃO OU VALIDAÇÃO | 2 |
| CONCLUÍDA, AGUARDANDO VALIDAÇÃO | 2 |
| SUBSTITUÍDA POR NOVA ESTRUTURA | 1 |
| **Total** | **26** |

## Riscos que permanecem

1. Ausência de organização/clínica explícita e isolamento multi-tenant completo.
2. Infraestrutura de mídia da telemedicina ainda não integrada.
3. IA clínica permanece somente planejada/condicionada por feature flag.
4. Cobertura frontend inferior à cobertura backend.
5. Storage privado, provedores de comunicação, backup e observabilidade dependem do ambiente de produção.
6. Dívida de tipagem permanece nos módulos historicamente excluídos pelo `mypy`; esta auditoria não amplia os ignores.

## Próximos blocos recomendados

1. Integrar e validar esta estabilização de autenticação e CI.
2. Implementar organizações, memberships e isolamento por tenant.
3. Reconciliar as issues de billing com o código atual e encerrar apenas as que tiverem todos os critérios comprovados.
4. Finalizar os trabalhos de `core` sem misturar escopos.
5. Executar uma rodada posterior de fechamento do backlog usando os relatórios dos workflows e os commits integrados como evidência.

[Voltar](README.md)
