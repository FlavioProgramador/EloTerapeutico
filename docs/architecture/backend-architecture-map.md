# Organização arquitetural do backend

## Princípio

Cada app mantém na raiz apenas entrypoints convencionais do Django e arquivos que
representam contratos públicos. Regras transacionais ficam em `services/`, consultas
reutilizáveis e sensíveis em `selectors/`, e a adaptação HTTP em `api/` ou `actions/`.

A divisão é aplicada somente onde existe complexidade real. CRUDs pequenos não recebem
pastas artificiais.

## Estrutura atual

```text
backend/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── core/
│   │   ├── audit.py
│   │   ├── exceptions.py
│   │   ├── fields.py
│   │   ├── integrations/
│   │   │   └── notifications.py
│   │   ├── pagination.py
│   │   └── validators.py
│   ├── users/
│   │   ├── api/
│   │   │   ├── password_reset_views.py
│   │   │   ├── serializers.py
│   │   │   └── views.py
│   │   ├── services/
│   │   │   └── credentials.py
│   │   ├── models.py
│   │   └── urls.py
│   ├── patients/
│   │   ├── actions/
│   │   │   ├── imports.py
│   │   │   └── metrics.py
│   │   ├── api/
│   │   ├── selectors/
│   │   │   ├── dashboard.py
│   │   │   └── patients.py
│   │   ├── services/
│   │   │   ├── imports.py
│   │   │   └── lifecycle.py
│   │   └── tests/
│   ├── records/
│   │   ├── api/
│   │   │   ├── evolution_views.py
│   │   │   ├── evolution_serializers.py
│   │   │   ├── evolution_attachment_list_views.py
│   │   │   ├── evolution_attachment_detail_views.py
│   │   │   └── evolution_template_views.py
│   │   ├── models/
│   │   ├── selectors/
│   │   │   └── evolutions.py
│   │   ├── services/
│   │   │   └── evolutions.py
│   │   ├── management/
│   │   └── tests/
│   ├── agenda/
│   │   ├── api/
│   │   ├── model_parts/
│   │   ├── serializer_parts/
│   │   ├── view_parts/
│   │   └── tests/
│   └── financeiro/
│       ├── api/
│       │   ├── transaction_viewset.py
│       │   ├── transaction_payment_actions.py
│       │   ├── transaction_state_actions.py
│       │   ├── transaction_list_actions.py
│       │   └── transaction_report_actions.py
│       ├── selectors/
│       │   └── transactions.py
│       ├── services/
│       │   ├── payments.py
│       │   ├── cancellations.py
│       │   ├── reversals.py
│       │   └── exports.py
│       └── tests/
├── core/
│   └── compatibilidade para migrations e imports históricos
└── tests/
```

## Services implementados

### Prontuário

`apps.records.services.evolutions` centraliza criação, atualização, versionamento,
arquivamento e anexos. Operações com múltiplas escritas utilizam transações atômicas.
As views continuam responsáveis por permissões HTTP, serialização e auditoria.

### Pacientes

`apps.patients.services.lifecycle` controla desativação e restauração. A desativação
preserva o contrato existente: status inativo, cadastro fora das consultas comuns e
`deleted_at` preenchido.

`apps.patients.services.imports` valida e importa CSVs com limite defensivo, detecção de
duplicidades, preview e confirmação transacional.

### Financeiro

`apps.financeiro.services.payments` registra pagamento e confirma a consulta associada
na mesma transação. `apps.financeiro.services.cancellations` e
`apps.financeiro.services.reversals` centralizam cancelamento e estorno com bloqueio de
linha. `apps.financeiro.services.exports` produz CSV com proteção contra injeção de
fórmulas.

### Usuários

`apps.users.services.credentials` gera o token e a URL de recuperação sem expor a
existência da conta. O envio externo é delegado a
`apps.infrastructure.messaging.email`.

## Selectors implementados

- `apps.records.selectors.evolutions`: evoluções autorizadas, opções de consultas e
  anexos ativos, com `select_related` e `prefetch_related`.
- `apps.patients.selectors.patients`: isolamento por profissional e suporte a registros
  arquivados.
- `apps.patients.selectors.dashboard`: métricas agregadas do painel.
- `apps.financeiro.selectors.transactions`: visibilidade por função, pendências,
  resumo mensal e consultas não faturadas.

## Consolidação do prontuário

Os arquivos `evolution_flow_views_v2.py` e `evolution_flow_serializers_v2.py` foram
consolidados em módulos canônicos dentro de `records/api/` e removidos. As URLs e os
formatos utilizados pelo frontend foram preservados.

## Segurança

- Querysets de pacientes e transações são restringidos antes da busca por ID.
- Evoluções confidenciais continuam filtradas por autor ou permissão específica.
- Downloads de anexos validam o vínculo com a evolução e a autorização clínica.
- Importação CSV é limitada a terapeutas e executada atomicamente.
- Pagamento e sincronização da consulta são atômicos.
- Cancelamento e estorno bloqueiam a linha da transação durante a mudança de estado.
- Recuperação de senha retorna mensagem neutra para evitar enumeração de usuários.
- Auditoria permanece na borda HTTP e não registra o conteúdo clínico completo.

## Compatibilidade

- Migrations históricas não foram reescritas.
- App labels, tabelas e endpoints públicos permanecem iguais.
- `apps.core` é a implementação oficial da infraestrutura compartilhada.
- `backend/core` permanece apenas para imports históricos serializados por migrations.
- `records.extended_models` e `records.treatment_models` permanecem como wrappers de
  compatibilidade até a remoção segura de todos os consumidores.

## Decisões deliberadamente adiadas

- Renomear `config` para `config`: ganho apenas estético e alto impacto.
- Reorganizar integralmente `agenda/model_parts`, `serializer_parts` e `view_parts`:
  deve ocorrer em PR isolada após os fluxos críticos permanecerem verdes.
- Remover wrappers históricos: somente após confirmar que nenhuma migration ou
  integração depende dos caminhos antigos.
