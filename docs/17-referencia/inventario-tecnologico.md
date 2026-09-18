# Inventário tecnológico

Este documento registra tecnologias encontradas no código, arquivos de dependências, imagens Docker e workflows do commit `75827a2dbfe7d4f86f0865f05d9a5a8f660e0f78`.

Versões devem ser atualizadas quando `requirements*.txt`, `package.json`, Dockerfiles ou workflows forem alterados.

## Linguagens e formatos

| Tecnologia | Uso |
| --- | --- |
| Python | Backend Django, Celery, scripts, testes e validações |
| TypeScript | Frontend Next.js, BFF, componentes, hooks, services e tipos |
| JavaScript | Configurações, testes Node e dependências frontend |
| SQL | PostgreSQL, migrations, constraints, índices e consultas administrativas controladas |
| HTML | Templates Django, e-mail e renderização frontend |
| CSS | Tailwind CSS, estilos globais e componentes |
| Shell | Dockerfiles, Compose, CI e comandos operacionais |
| YAML | Docker Compose e GitHub Actions |
| JSON | APIs, configuração de pacotes, payloads e Celery |
| Markdown | Documentação técnica e relatórios |
| Mermaid | Diagramas de arquitetura, fluxos e estados |

## Runtime backend

| Tecnologia | Versão/faixa | Finalidade | Ambiente |
| --- | --- | --- | --- |
| Python | 3.12 | Runtime do backend e workers | Todos |
| Django | `>=6.0.7,<6.1` | Framework web, ORM, Admin e configurações | Todos |
| Django REST Framework | `>=3.17.1,<3.18` | API REST, serializers, permissions e paginação | Todos |
| PostgreSQL | 15 no Compose/CI | Persistência transacional | Todos |
| Redis | 7 no Compose | Broker, resultados, cache e rate limit | Dev/prod |
| Celery | `>=5.4,<5.6` | Processamento assíncrono e tarefas periódicas | Dev/prod |
| Gunicorn | `>=22.0,<23.0` | Servidor WSGI da imagem de produção | Produção |

## Bibliotecas backend compartilhadas

| Dependência | Versão/faixa | Uso |
| --- | --- | --- |
| `django-cors-headers` | `>=4.3,<4.4` | CORS e headers permitidos |
| `django-filter` | `>=24.1,<24.2` | Filtros da API |
| `django-environ` | `>=0.14.0,<0.15` | Leitura e tipagem de variáveis de ambiente |
| `httpx` | `>=0.28,<0.29` | Clients HTTP, incluindo integrações |
| `python-dateutil` | `>=2.9,<3.0` | Datas, recorrências e utilitários |
| `sqlparse` | `>=0.5.5,<0.6` | Parsing SQL usado pelo ecossistema Django |
| `redis` | `>=5.0,<6.0` | Cliente Redis e integração Celery |
| `livekit-api` | `>=1.2.0,<1.3` | Salas, participantes, tokens e webhooks LiveKit |
| `django-unfold` | `>=0.96,<0.97` | Backoffice e tema do Django Admin |
| `djangorestframework-simplejwt` | `>=5.5.1,<6.0` | JWT, rotação e blacklist |
| `psycopg2-binary` | `>=2.9,<3.0` | Driver PostgreSQL |
| `cryptography` | `>=49.0.0,<50.0` | Criptografia de campos e tokens técnicos |
| `drf-spectacular` | `>=0.29.0,<0.30` | Schema OpenAPI, Swagger e ReDoc |
| `argon2-cffi` | `>=23.1,<23.2` | Password hashing Argon2 |
| `weasyprint` | `>=69.0,<70.0` | PDFs de prontuário, documentos e recibos |
| `azure-storage-blob` | `>=12.19,<12.20` | SDK de acesso ao Azure Blob |
| `django-ratelimit` | `>=4.1,<4.2` | Rate limiting |

## Dependências de produção

Estas dependências estão em `backend/requirements-prod.txt` e não devem ser omitidas do inventário por não aparecerem no arquivo consolidado de desenvolvimento.

| Dependência | Versão/faixa | Uso |
| --- | --- | --- |
| `structlog` | `>=24.1,<24.2` | Logging estruturado em JSON |
| `django-health-check` | `>=3.18,<3.19` | Verificações de dependências do runtime |
| `whitenoise` | `>=6.6,<6.7` | Arquivos estáticos comprimidos e versionados |
| `django-storages[azure]` | `>=1.14,<1.15` | Backend `AzureStorage` do Django |

## Bibliotecas nativas da imagem backend

O Dockerfile instala:

- `build-essential`;
- `libpq-dev`;
- `libpango-1.0-0`;
- `libpangoft2-1.0-0`.

Elas suportam compilação de dependências, PostgreSQL e renderização do WeasyPrint. Execução fora do Docker precisa de equivalentes do sistema operacional.

## Frontend

| Tecnologia | Versão | Finalidade |
| --- | --- | --- |
| Node.js | 24 na imagem | Runtime de build e servidor Next.js |
| Next.js | 16.2.11 | App Router, SSR, Route Handlers e BFF |
| React | 19.2.7 | Interface baseada em componentes |
| React DOM | 19.2.4 | Renderização web |
| TypeScript | 6 | Tipagem estática |
| Tailwind CSS | 4 | Design tokens e estilos utilitários |
| TanStack Query | 5.101.2 | Estado remoto, cache e invalidação |
| Axios | 1.18.1 | Cliente HTTP do BFF |
| React Hook Form | 7.80.0 | Estado e validação de formulários |
| Zod | 4.4.3 | Schemas e validação de dados |

## Componentes e experiência frontend

| Dependência | Versão/faixa | Uso |
| --- | --- | --- |
| `@hookform/resolvers` | `^5.4.0` | Integração React Hook Form e schemas |
| `@radix-ui/react-dialog` | `^1.1.17` | Diálogos acessíveis |
| `@radix-ui/react-label` | `^2.1.11` | Labels acessíveis |
| `@radix-ui/react-select` | `^2.3.1` | Selects acessíveis |
| `@radix-ui/react-separator` | `^1.1.11` | Separadores |
| `@radix-ui/react-slot` | `^1.3.0` | Composição de componentes |
| `@radix-ui/react-tooltip` | `^1.2.12` | Tooltips acessíveis |
| `lucide-react` | `^1.23.0` | Ícones |
| `framer-motion` | `^12.41.0` | Animações e transições |
| `sonner` | `^2.0.7` | Toasts e feedback |
| `next-themes` | `^0.4.6` | Tema da interface |
| `cookies-next` | `^6.1.1` | Utilitários de cookie |
| `date-fns` | `^4.4.0` | Datas e formatação |
| `clsx` | `^2.1.1` | Composição de classes |
| `tailwind-merge` | `^3.6.0` | Resolução de classes Tailwind |

## Telemedicina frontend

| Dependência | Versão/faixa | Uso |
| --- | --- | --- |
| `livekit-client` | `^2.20.2` | Conexão WebRTC/WSS |
| `@livekit/components-react` | `^2.9.23` | Componentes React de chamada |
| `@livekit/components-styles` | `^1.2.0` | Estilos base LiveKit |

## Banco de dados e persistência

### PostgreSQL

Responsável por:

- usuários e autenticação;
- organizações e memberships;
- pacientes e prontuários;
- agenda e telemedicina lógica;
- financeiro e Billing;
- documentos e formulários;
- comunicações e tentativas;
- auditoria;
- estados duráveis dos jobs.

### Redis

Responsável por:

- broker Celery;
- resultados temporários;
- cache em produção;
- backend do rate limit em produção.

Redis não substitui o PostgreSQL como fonte oficial dos estados de negócio.

### Storage

- filesystem no desenvolvimento;
- Azure Blob privado configurável em produção;
- URLs temporárias;
- arquivos estáticos por WhiteNoise em produção.

## Containers e processos

| Tecnologia/processo | Uso |
| --- | --- |
| Docker | Construção das imagens |
| Docker Compose | Ambiente local e validação da topologia |
| Gunicorn | Servidor padrão da imagem backend |
| Next.js server | `next start` na imagem e `next dev` no Compose |
| Celery worker `default` | Billing, scheduling e tarefas gerais |
| Celery worker `exports` | Exportações clínicas |
| Celery worker `uploads` | Verificação de uploads |
| Celery worker `communications` | Comunicações e automações |
| Celery Beat | Tarefas periódicas |
| Volumes Docker | PostgreSQL, Redis, staticfiles e schedule do Beat |

## Serviços externos

| Serviço | Uso | Status documental |
| --- | --- | --- |
| Asaas | Billing, checkout, cobrança, webhooks e reconciliação | Implementação presente; staging pendente |
| LiveKit | Áudio e vídeo WebRTC, salas, tokens e webhooks | Implementação presente; desativado por padrão |
| Azure Blob | Documentos e mídia privada | Configurável; infraestrutura não comprovada |
| SMTP/SendGrid | Recuperação, convites e comunicações | Configurável |
| WhatsApp manual | Link `wa.me` e confirmação humana | Implementado |
| WhatsApp Business | Canal oficial | Interface preparada; provider operacional não comprovado |
| SMS | Canal alternativo | Interface preparada; provider não definido |
| GitHub Actions | CI, segurança e validação | Implementado |
| Provedor de IA | Assistência futura | Não definido nem implementado |

## Testes backend

| Ferramenta | Versão/faixa | Uso |
| --- | --- | --- |
| pytest | `>=9.0.3,<10.0` | Runner principal |
| pytest-django | `>=4.8,<5.0` | Integração Django |
| pytest-cov | `>=5.0,<7.0` | Cobertura |
| factory-boy | `>=3.3,<3.4` | Factories |
| Faker | `>=24.0,<24.1` | Dados sintéticos |

## Qualidade backend

| Ferramenta | Versão/faixa | Uso |
| --- | --- | --- |
| Ruff | `>=0.15,<0.16` | Lint e qualidade |
| mypy | `>=1.18,<2.0` | Tipagem estática |
| django-stubs | `>=5.2,<6.0` | Tipagem do Django |
| pre-commit | `>=3.7,<4.0` | Hooks locais |
| script arquitetural | interno | Fronteiras, módulos e padrões dos apps |
| drf-spectacular CLI | dependência existente | Validação do OpenAPI |

## Testes e qualidade frontend

| Ferramenta | Versão/faixa | Uso |
| --- | --- | --- |
| ESLint | `^9` | Lint |
| eslint-config-next | `16.2.11` | Regras Next.js |
| TypeScript compiler | 6 | `tsc --noEmit` |
| Node Test Runner | Node 24 | Testes `.mjs` e cobertura experimental |
| Playwright | pacote isolado em `frontend/e2e` | Autenticação e gateway E2E |
| TanStack Query Devtools | `^5.101.2` | Diagnóstico local |

## Scripts frontend

| Script | Finalidade |
| --- | --- |
| `npm run dev` | Next.js em desenvolvimento |
| `npm run build` | Build de produção |
| `npm run start` | Servidor do build |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript sem emissão |
| `npm test` | Testes Node |
| `npm run test:coverage` | Cobertura com thresholds configurados |
| `npm run test:agenda` | Testes de agenda |
| `npm run test:auth` | Testes unitários de autenticação/BFF |
| `npm run test:e2e` | E2E isolado |
| `npm run test:e2e:auth` | Autenticação E2E |
| `npm run test:e2e:gateway` | Gateway E2E |

## GitHub Actions

Workflows encontrados incluem:

| Workflow | Finalidade |
| --- | --- |
| `django-ci.yml` | Migrations, checks, lint, tipagem e testes backend |
| `frontend-ci.yml` | Instalação, lint, typecheck, testes e build frontend |
| `auth-e2e.yml` | Backend, frontend e autenticação/gateway E2E reais |
| `test-coverage.yml` | Cobertura e artefatos de teste |
| `billing-validation.yml` | Contratos e fluxos de Billing |
| `docs-validation.yml` | Links, Markdown, secrets e consistência documental |
| `docker-images.yml` | Build e validação de imagens |
| `codeql.yml` | Análise estática de segurança |
| `dependency-review.yml` | Revisão de novas dependências em PR |
| `backend-security.yml` | Bandit, pip-audit e controles backend |
| `dependency-security.yml` | Auditoria Python e npm |

## Observações de versão

1. Faixas vêm dos manifests; versões resolvidas podem ser consultadas nos lockfiles.
2. Dependências de produção não devem ser inferidas somente de `requirements.txt`.
3. A documentação não deve declarar deploy automático porque os workflows atuais validam e constroem, mas não provam implantação.
4. Antes de atualizar uma versão, valide compatibilidade, lockfile, testes e advisories de segurança.

[Voltar](README.md)
