# Estrutura de pastas

```text
backend/
├── apps/
│   ├── core/
│   ├── users/
│   ├── patients/
│   ├── records/
│   ├── scheduling/
│   ├── finances/
│   ├── documents/
│   ├── reports/
│   ├── forms/
│   ├── billing/
│   ├── communications/
│   └── audit/
└── config/
```

## Regras de organização

- `apps/core` contém somente recursos transversais ao backend Django;
- regras de negócio pertencem aos `services` do domínio responsável;
- consultas complexas e reutilizáveis pertencem a `selectors`;
- views e serializers permanecem na camada `api`;
- migrations e labels Django são preservados durante reorganizações de arquivos.
