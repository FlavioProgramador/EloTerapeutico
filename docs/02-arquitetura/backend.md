# Backend

## Stack e inicialização

O backend usa Python e Django. `manage.py` seleciona `config.settings.development` por padrão. O WSGI é servido por Gunicorn na imagem de produção, enquanto o Docker Compose de desenvolvimento usa `runserver`.

## Camadas

| Camada | Responsabilidade | Exemplos |
| --- | --- | --- |
| Models | Persistência, constraints e transições locais | `apps/*/models.py`, `model_parts/` |
| Serializers | Validação de entrada e representação | `apps/*/api/serializers/` |
| Views/ViewSets | Contrato HTTP e orquestração | `apps/*/api/views/` |
| Services/actions | Regras e operações de domínio | `services/`, `actions/` |
| Selectors | Querysets e leitura otimizada | `selectors/` |
| Permissions | Autorização HTTP/objeto | `api/permissions.py` |
| Core | paginação, exceções, auditoria, campos e validadores | `backend/apps/core/` |
| Infrastructure | integrações e infraestrutura compartilhada | `backend/apps/core/infrastructure/` |

## Configuração DRF

- autenticação JWT global;
- permissão global `IsAuthenticated`;
- filtros Django, busca e ordenação;
- paginação padrão de 20 itens;
- schema OpenAPI por drf-spectacular;
- exception handler customizado.

Endpoints públicos declaram `AllowAny` explicitamente, como login, cadastro, planos, health check e webhook.

## Configurações por ambiente

- `base.py`: componentes compartilhados;
- `dev.py`: DEBUG, CORS aberto, e-mail no console e rate limit desabilitado;
- `test.py`: SQLite, hasher rápido e storage temporário;
- `prod.py`: HTTPS, HSTS, CORS explícito, Redis, WhiteNoise, SMTP e validação forte de segredos.

## Administração

Django Unfold organiza dashboard, SQL Explorer, pacientes, registros, agenda, financeiro, billing, usuários, auditoria, documentos e formulários. O backoffice deve ser protegido por autenticação forte, rede restrita quando possível e revisão periódica de `is_staff`/`is_superuser`.

## Pontos de atenção

- `apps.audit.services.access_logging.log_access` não interrompe a ação de negócio quando a gravação da auditoria falha; isso preserva disponibilidade, mas exige alerta operacional;
- há imports de compatibilidade para modelos e URLs após refatorações;
- vários módulos estão excluídos ou ignorados parcialmente pelo mypy;
- a rota de billing também existe em `/api/billing/`, além do prefixo principal.

[Voltar](README.md)
