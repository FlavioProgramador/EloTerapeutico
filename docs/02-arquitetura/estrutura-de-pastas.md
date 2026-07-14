# Estrutura de pastas

```text
backend/
├── apps/
│   ├── core/
│   ├── users/
│   ├── patients/
│   ├── records/
│   ├── agenda/
│   ├── financeiro/
│   ├── documents/
│   ├── reports/
│   ├── forms/
│   ├── billing/
│   ├── communications/
│   └── audit/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── infrastructure/
│   ├── payments/asaas/
│   └── messaging/
├── quality/
├── requirements/
└── manage.py
```

## Regras de organização

- `apps/core` contém somente recursos transversais ao backend Django.
- regras de negócio pertencem aos `services` do domínio responsável;
- consultas complexas e reutilizáveis pertencem a `selectors`;
- views e serializers devem permanecer na camada `api`;
- integrações HTTP externas pertencem a `infrastructure`;
- o pacote `config` é o único responsável por settings, URLs, ASGI e WSGI;
- migrations e labels Django são preservados durante reorganizações de arquivos.

[Voltar](README.md)

## Raiz simplificada do backend

A raiz versionada do backend deve conter somente duas pastas de código:

```text
backend/
├── apps/
├── config/
├── .dockerignore
├── .env.example
├── Dockerfile
├── Makefile
├── manage.py
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── requirements-prod.txt
└── startup.sh
```

- `apps/`: domínios, integrações específicas de domínio, templates e testes.
- `config/`: configuração Django e scripts operacionais.
- caches, ambientes virtuais, mídia e arquivos estáticos coletados são locais e ignorados pelo Git.
- execute `make clean` dentro de `backend/` para remover resíduos locais e pacotes legados.
