# Estrutura de pastas

```text
backend/
├── apps/
│   ├── users/
│   ├── patients/
│   ├── records/
│   ├── agenda/
│   ├── financeiro/
│   ├── documents/
│   ├── reports/
│   ├── forms/
│   ├── billing/
│   └── audit/
├── core/
├── infrastructure/
├── elo_terapeutico/
│   ├── settings/
│   └── urls.py
├── requirements/
├── quality/
└── manage.py

frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── contexts/
│   ├── features/
│   ├── lib/
│   └── types/
├── package.json
└── Dockerfile
```

## Regras de organização

- `models.py` pode atuar como fachada para `model_parts/`;
- APIs podem ser divididas em serializers, views, actions e permissions;
- regras reutilizáveis pertencem a services/actions, não a componentes de interface;
- selectors concentram queries e isolamento de dados;
- componentes frontend específicos ficam dentro da feature correspondente;
- configurações de ambiente não devem conter segredos versionados.

[Voltar](README.md)
