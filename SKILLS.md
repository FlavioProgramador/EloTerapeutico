# 🧠 Skills Essenciais – Elo Terapêutico

Este documento consolida as competências técnicas necessárias para desenvolver, manter e evoluir o **Elo Terapêutico**. Use-o como guia de aprendizado e referência durante o desenvolvimento.

---

## 🐍 Backend (Django)

### Core
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Python 3.10+ (sintaxe, tipagem, async) | ⭐⭐⭐⭐ Avançado | [python.org/docs](https://docs.python.org/3/) |
| Django 5.x (Models, Views, ORM, Admin) | ⭐⭐⭐⭐ Avançado | [djangoproject.com/docs](https://docs.djangoproject.com/en/5.0/) |
| Django Rest Framework (serializers, viewsets, routers) | ⭐⭐⭐⭐ Avançado | [django-rest-framework.org](https://www.django-rest-framework.org/) |
| Autenticação JWT com SimpleJWT | ⭐⭐⭐ Intermediário | [SimpleJWT Docs](https://django-rest-framework-simplejwt.readthedocs.io/) |
| Permissões e RBAC (roles, políticas de acesso) | ⭐⭐⭐ Intermediário | DRF Permissions Docs |
| Django Custom User Model | ⭐⭐⭐ Intermediário | Django Docs |
| Settings por ambiente (dev/prod) | ⭐⭐⭐ Intermediário | Django Best Practices |

### Banco de Dados
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| PostgreSQL (queries, índices, constraints) | ⭐⭐⭐ Intermediário | [postgresql.org/docs](https://www.postgresql.org/docs/) |
| Django ORM (queries complexas, select_related, prefetch) | ⭐⭐⭐⭐ Avançado | Django ORM Docs |
| Migrações Django (gestão, squash, rollback) | ⭐⭐⭐ Intermediário | Django Migrations |
| Transações atômicas (`atomic()`) | ⭐⭐⭐ Intermediário | Django DB Transactions |

### Segurança & LGPD
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Criptografia simétrica (AES-256 via `django-cryptography`) | ⭐⭐⭐ Intermediário | [django-cryptography Docs](https://django-cryptography.readthedocs.io/) |
| Hashing seguro de senhas (Argon2, BCrypt) | ⭐⭐⭐ Intermediário | Django Docs – Password Hashing |
| CORS (django-cors-headers) | ⭐⭐ Básico | [django-cors-headers](https://github.com/adamchainz/django-cors-headers) |
| Audit Trail / Logging de Acesso | ⭐⭐⭐ Intermediário | Python Logging Docs |
| Conformidade com LGPD | ⭐⭐⭐ Intermediário | [LGPD – Gov.br](https://www.gov.br/lgpd) |

### API & Documentação
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Design de APIs RESTful | ⭐⭐⭐ Intermediário | REST API Best Practices |
| OpenAPI / Swagger via `drf-spectacular` | ⭐⭐ Básico | [drf-spectacular](https://drf-spectacular.readthedocs.io/) |
| Paginação, Filtragem e Busca no DRF | ⭐⭐⭐ Intermediário | DRF Filtering |

---

## ⚛️ Frontend (Next.js)

### Core
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| TypeScript (tipos, interfaces, generics) | ⭐⭐⭐⭐ Avançado | [typescriptlang.org/docs](https://www.typescriptlang.org/docs/) |
| React 18+ (hooks, context, Suspense) | ⭐⭐⭐⭐ Avançado | [react.dev](https://react.dev/) |
| Next.js 14+ App Router (layouts, loading, error) | ⭐⭐⭐⭐ Avançado | [nextjs.org/docs](https://nextjs.org/docs) |
| Server Components vs. Client Components | ⭐⭐⭐ Intermediário | Next.js Docs |
| Server Actions e Route Handlers | ⭐⭐⭐ Intermediário | Next.js Server Actions |
| Middleware (proteção de rotas autenticadas) | ⭐⭐⭐ Intermediário | Next.js Middleware |

### UI & Estilização
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Tailwind CSS (layout, responsividade, dark mode) | ⭐⭐⭐⭐ Avançado | [tailwindcss.com/docs](https://tailwindcss.com/docs) |
| Shadcn UI + Radix UI (componentes acessíveis) | ⭐⭐⭐ Intermediário | [ui.shadcn.com](https://ui.shadcn.com/) |
| Design Responsivo e Mobile-First | ⭐⭐⭐ Intermediário | CSS Flexbox/Grid |
| Acessibilidade Web (WCAG 2.1) | ⭐⭐ Básico | [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility) |

### Gerenciamento de Dados
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Fetch API / Axios (calls para a API Django) | ⭐⭐⭐ Intermediário | Axios Docs |
| TanStack Query (cache, refetch, mutations) | ⭐⭐⭐ Intermediário | [tanstack.com/query](https://tanstack.com/query/latest) |
| Cookies HttpOnly para armazenamento de JWT | ⭐⭐⭐ Intermediário | MDN – Cookies |
| Zustand ou Context API (estado global leve) | ⭐⭐ Básico | Zustand Docs |

---

## ☁️ Cloud & Azure

| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Azure App Service (deploy, variáveis de ambiente, logs) | ⭐⭐⭐ Intermediário | [Azure App Service Docs](https://learn.microsoft.com/en-us/azure/app-service/) |
| Azure Database for PostgreSQL (Flexible Server) | ⭐⭐ Básico | [Azure PostgreSQL Docs](https://learn.microsoft.com/en-us/azure/postgresql/) |
| Azure Blob Storage (upload, SAS URL, permissões) | ⭐⭐⭐ Intermediário | [Azure Blob Docs](https://learn.microsoft.com/en-us/azure/storage/blobs/) |
| Azure Static Web Apps (deploy do Next.js estático) | ⭐⭐ Básico | Azure Static Web Apps Docs |
| Configuração de HTTPS e Custom Domain na Azure | ⭐⭐ Básico | Azure Docs |
| Azure CLI (gerenciamento de recursos via terminal) | ⭐⭐ Básico | [Azure CLI Docs](https://learn.microsoft.com/en-us/cli/azure/) |
| Gerenciamento de Créditos Azure for Students | ⭐⭐ Básico | [Azure for Students](https://azure.microsoft.com/en-us/free/students/) |

---

## 🐳 Docker & Infraestrutura

| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Docker (build, imagens, containers, volumes) | ⭐⭐⭐ Intermediário | [docs.docker.com](https://docs.docker.com/) |
| Docker Compose (orquestração de múltiplos serviços) | ⭐⭐⭐ Intermediário | [Docker Compose Docs](https://docs.docker.com/compose/) |
| Escrita de Dockerfile eficiente (layer caching, multi-stage builds) | ⭐⭐⭐ Intermediário | Dockerfile Best Practices |
| `.dockerignore` e otimização de imagens | ⭐⭐ Básico | Docker Docs |
| Redes Docker (comunicação entre containers) | ⭐⭐ Básico | Docker Networking |

---

## 🔄 CI/CD & DevOps

| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Git (branching, rebase, stash, cherry-pick) | ⭐⭐⭐⭐ Avançado | [git-scm.com](https://git-scm.com/doc) |
| Conventional Commits + Semantic Versioning | ⭐⭐ Básico | [conventionalcommits.org](https://www.conventionalcommits.org/) |
| GitHub Actions (workflows, jobs, secrets, artifacts) | ⭐⭐⭐ Intermediário | [GitHub Actions Docs](https://docs.github.com/en/actions) |
| Deploy automático na Azure via GitHub Actions | ⭐⭐⭐ Intermediário | Azure Deploy Action |
| Gestão de Secrets no GitHub (GitHub Secrets) | ⭐⭐ Básico | GitHub Encrypted Secrets |

---

## 🧪 Testes

### Backend (Django)
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Testes unitários com `pytest-django` | ⭐⭐⭐ Intermediário | [pytest-django](https://pytest-django.readthedocs.io/) |
| Testes de API REST (endpoints, status codes, payloads) | ⭐⭐⭐ Intermediário | DRF Testing Docs |
| Factory Boy (geração de fixtures de teste) | ⭐⭐ Básico | [FactoryBoy Docs](https://factoryboy.readthedocs.io/) |
| Coverage (medição de cobertura de testes) | ⭐⭐ Básico | [coverage.py](https://coverage.readthedocs.io/) |

### Frontend (Next.js)
| Skill | Nível Recomendado | Recursos |
|-------|:-----------------:|----------|
| Jest + Testing Library (testes de componentes React) | ⭐⭐⭐ Intermediário | [testing-library.com](https://testing-library.com/) |
| Testes End-to-End com Playwright ou Cypress | ⭐⭐ Básico | [playwright.dev](https://playwright.dev/) |
| Mocking de chamadas HTTP (MSW – Mock Service Worker) | ⭐⭐ Básico | [mswjs.io](https://mswjs.io/) |

---

## 🛠️ Ferramentas & DX (Developer Experience)

| Ferramenta | Propósito | Recursos |
|------------|-----------|----------|
| `black` + `flake8` | Formatação e lint do código Python | Black Docs |
| `isort` | Ordenação automática de imports Python | isort Docs |
| `pre-commit` | Hooks de lint/formatação antes do commit | [pre-commit.com](https://pre-commit.com/) |
| `ESLint` + `Prettier` | Lint e formatação do código TypeScript/React | ESLint Docs |
| VS Code + extensões (Pylance, ESLint, Tailwind, Docker) | IDE e produtividade | [code.visualstudio.com](https://code.visualstudio.com/) |
| Postman ou Insomnia | Testes manuais da API Django | [postman.com](https://www.postman.com/) |

---

## 📊 Referência de Níveis

| Ícone | Nível | Descrição |
|-------|-------|-----------|
| ⭐⭐ | Básico | Entende os conceitos fundamentais e consegue usar com ajuda da documentação. |
| ⭐⭐⭐ | Intermediário | Usa de forma independente e resolve problemas comuns sem consulta constante. |
| ⭐⭐⭐⭐ | Avançado | Domina a ferramenta, aplica boas práticas e consegue tomar decisões de arquitetura. |

---

> 📌 **Nota:** As habilidades marcadas como **Avançado** são as mais críticas para o core do projeto (Django API + Next.js App Router). As demais podem ser aprendidas progressivamente ao longo das sprints definidas no [ROADMAP.MD](./ROADMAP.MD).
