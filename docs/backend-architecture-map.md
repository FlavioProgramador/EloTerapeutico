# Organização arquitetural do backend

## Princípio

Cada app deve manter no nível raiz apenas entrypoints convencionais do Django,
como `apps.py`, `admin.py`, `urls.py`, `models.py` quando pequeno, `migrations/`
e `tests/`. Implementações maiores são agrupadas por responsabilidade.

## Estrutura adotada

```text
backend/
├── elo_terapeutico/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── core/
│   │   ├── audit.py
│   │   ├── exceptions.py
│   │   ├── fields.py
│   │   ├── pagination.py
│   │   └── validators.py
│   ├── users/
│   │   ├── api/
│   │   │   ├── serializers.py
│   │   │   └── views.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── patients/
│   │   ├── actions/
│   │   ├── api/
│   │   ├── selectors/
│   │   ├── services/
│   │   ├── models.py
│   │   └── tests/
│   ├── records/
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── clinical.py
│   │   │   └── treatment.py
│   │   ├── management/
│   │   ├── migrations/
│   │   └── tests/
│   ├── agenda/
│   │   ├── api/
│   │   ├── model_parts/
│   │   ├── serializer_parts/
│   │   ├── view_parts/
│   │   └── tests/
│   └── financeiro/
│       ├── api/
│       ├── models.py
│       └── tests/
├── core/
│   └── compatibilidade para migrations e imports históricos
└── tests/
```

## Decisões aplicadas

- `apps.core` é a implementação oficial dos recursos compartilhados.
- O antigo `backend/core` contém somente reexports mínimos para não quebrar
  migrations já aplicadas.
- O app `users` concentra a camada HTTP em `api/`.
- O app `patients` concentra mixins e casos de uso HTTP em `actions/`.
- O app `records` usa um pacote `models/` em vez de um `models.py` monolítico.
- O app `financeiro` mantém a implementação em `api/` e remove wrappers do topo.
- Não são criadas pastas vazias apenas para imitar outra arquitetura.
- Migrations, app labels, nomes de tabelas e endpoints públicos permanecem
  preservados.

## Compatibilidade

Alguns módulos antigos permanecem temporariamente quando seus caminhos foram
serializados por migrations ou podem ser importados por integrações existentes.
Esses módulos devem conter apenas imports explícitos para a implementação nova.
Código novo não deve importar de `core.*`, `records.extended_models` ou
`records.treatment_models`.

## Próximas consolidações

1. renomear gradualmente as pastas genéricas da agenda sem alterar imports em
   uma única mudança de alto risco;
2. agrupar serializers clínicos em `records/api/serializers/`;
3. agrupar views clínicas em `records/api/views/`;
4. mover operações financeiras transacionais para `services/`;
5. remover compatibilidades somente após busca de consumidores e CI verde.
