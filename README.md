# Elo Terapêutico

Plataforma web de gestão para profissionais de saúde e terapeutas, com agenda, pacientes, prontuário eletrônico, telemedicina, financeiro clínico, documentos, formulários, comunicações, relatórios e cobrança de assinaturas.

> **Situação atual:** desenvolvimento ativo e pré-produção. A base funcional é ampla, mas integrações externas e controles operacionais ainda precisam ser validados antes do uso com dados clínicos reais.

## Índice

- [Visão geral](#visão-geral)
- [Módulos](#módulos)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Início rápido](#início-rápido)
- [Docker](#docker)
- [Testes e qualidade](#testes-e-qualidade)
- [Segurança e dados clínicos](#segurança-e-dados-clínicos)
- [Documentação](#documentação)
- [Contribuição](#contribuição)
- [Limitações conhecidas](#limitações-conhecidas)

## Visão geral

O Elo Terapêutico centraliza tarefas administrativas e clínicas que normalmente ficam distribuídas entre agendas, planilhas, arquivos e sistemas de cobrança. O público principal é composto por terapeutas e profissionais que realizam atendimentos individuais, presenciais, híbridos ou remotos.

O domínio `apps.organizations` fornece organização, memberships, papéis e configurações para isolamento multi-tenant. Alguns módulos legados ainda precisam de revisão transversal antes que a plataforma seja considerada pronta para clínicas com equipes complexas.

## Módulos

| Módulo | Situação resumida |
| --- | --- |
| Autenticação e usuários | JWT, rotação, blacklist, lockout, reset e BFF Next.js com cookies HttpOnly e CSRF |
| Organizações | Tenant explícito, memberships, papéis, onboarding e configurações institucionais |
| Pacientes | Cadastro, responsáveis, status, importação/exportação e arquivamento lógico |
| Prontuário | Anamnese, evoluções, aditivos, documentos, anexos, metas e exportações |
| Agenda | Consultas, recorrências, salas, bloqueios, pacotes e lembretes |
| Telemedicina | Áudio e vídeo LiveKit, convites com hash, consentimento, E2EE e webhooks; depende de configuração e staging |
| Financeiro clínico | Receitas, despesas, mensalidades, pagamentos e relatórios |
| Documentos | Modelos, biblioteca, geração e integridade por hash; storage privado depende da infraestrutura |
| Formulários | Construtor, templates, submissões e respostas |
| Comunicações | Notificações, templates, automações, Celery e webhooks; canais externos dependem de provedores |
| Relatórios | Consultas, pacientes, financeiro, agendamento e exportações |
| Billing | Planos, preços, assinaturas, entitlements, pagamentos e integração configurável com Asaas |
| Auditoria | Trilha para ações sensíveis e sanitização de metadados |
| Administração | Django Admin e Django Unfold |
| Dashboard | Agregação frontend dos módulos, com cobertura parcial |
| Portal do paciente | Não implementado como domínio completo |
| Inteligência artificial | Planejada; existe somente flag comercial e placeholder, sem integração funcional |

Detalhes, maturidade e pendências estão na [matriz de módulos](docs/17-referencia/matriz-de-modulos.md).

## Arquitetura

```mermaid
flowchart LR
    U[Usuário] --> F[Next.js 16 / BFF]
    F -->|HTTPS / JSON| A[Django REST Framework]
    F -->|Bearer JWT somente no servidor| A
    A --> P[(PostgreSQL)]
    A --> S[Storage local ou Azure Blob]
    A --> G[Asaas]
    A --> L[LiveKit API]
    F -->|WebRTC / WSS com E2EE| L
    R[(Redis)] --> C[Celery]
    C --> EX[Exportações]
    C --> UP[Uploads]
    C --> CO[Comunicações]
    C --> BI[Billing]
    C --> TM[Manutenção de telemedicina]
```

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind CSS, TanStack Query e componentes LiveKit.
- **BFF:** Route Handlers guardam access/refresh em cookies `HttpOnly`, aplicam double-submit CSRF e limitam os endpoints públicos de telemedicina por origem confiável.
- **Backend:** Django, Django REST Framework, Simple JWT e abstração de provedor de mídia.
- **Banco:** PostgreSQL 15 no Docker e no CI principal; SQLite pode ser usado somente em cenários locais específicos.
- **Processamento assíncrono:** Redis, Celery workers separados e Celery Beat.
- **Arquivos:** filesystem no desenvolvimento; Azure Blob privado deve ser configurado em produção.
- **Telemedicina:** LiveKit fornece transporte WebRTC; o Elo Terapêutico controla autorização, convite, consentimento, E2EE e ciclo da sala.

Leia a [visão geral de arquitetura](docs/02-arquitetura/README.md), o [mapa dos apps](docs/architecture/backend-architecture-map.md) e as [convenções de camadas](docs/backend-architecture.md).

## Tecnologias

### Backend

- Python 3.12;
- Django `>=6.0.7,<6.1`;
- Django REST Framework `>=3.17.1,<3.18`;
- PostgreSQL 15;
- Redis e Celery;
- Simple JWT, django-filter, drf-spectacular e django-ratelimit;
- `livekit-api` para salas, participantes, tokens e webhooks;
- WeasyPrint para PDFs;
- cryptography/Fernet para campos textuais sensíveis;
- Django Unfold para o backoffice.

### Frontend

- Node.js 24;
- Next.js 16.2.9;
- React 19;
- TypeScript 6;
- Tailwind CSS 4;
- Axios, TanStack Query, React Hook Form e Zod;
- `livekit-client` e `@livekit/components-react`;
- Playwright isolado para autenticação E2E.

## Início rápido

### Requisitos

- Git;
- Python 3.12;
- Node.js 24;
- PostgreSQL 15+ ou ambiente Docker;
- Redis para Celery/cache;
- bibliotecas nativas do WeasyPrint quando executar fora do Docker.

### Backend sem Docker

```bash
cd backend
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Frontend sem Docker

```bash
cd frontend
npm ci
```

Crie `frontend/.env.local`:

```text
BACKEND_API_URL=http://localhost:8000/api/v1/
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/
```

Depois execute:

```bash
npm run dev
```

Acesse `http://localhost:3000`. A API fica em `http://localhost:8000/api/v1/` e a documentação OpenAPI em `http://localhost:8000/api/docs/`.

Para processamento assíncrono, execute workers/beat do Celery ou utilize o Docker Compose.

A telemedicina permanece desligada por padrão. Consulte a [operação de telemedicina](docs/12-operacao/telemedicina.md) antes de configurar LiveKit.

## Docker

Na raiz do repositório:

```bash
cp .env.example .env
# preencha POSTGRES_PASSWORD, REDIS_PASSWORD e os segredos obrigatórios
docker compose up --build
```

Serviços principais:

- frontend: porta `3000`;
- backend: porta `8000`;
- PostgreSQL: exposto apenas em `127.0.0.1:5432`;
- Redis: exposto apenas em `127.0.0.1:6379`;
- workers Celery para `default`, `exports` e `communications`;
- Celery Beat para tarefas periódicas.

Consulte o [guia Docker](docs/03-instalacao/instalacao-docker.md), a [operação de Comunicações](docs/05-modulos/comunicacoes/README.md) e a [operação de telemedicina](docs/12-operacao/telemedicina.md).

## Testes e qualidade

Backend:

```bash
cd backend
python apps/core/quality/check_backend_architecture.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
ruff check .
mypy .
pytest --create-db
```

O workflow principal executa migrations e testes sobre PostgreSQL 15. Ruff e mypy são gates obrigatórios.

Frontend:

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

Autenticação unitária:

```bash
npm run test:auth
```

Autenticação E2E, com aplicações já iniciadas e variáveis de usuário sintético configuradas:

```bash
cd frontend/e2e
npm install
npx playwright install chromium
npm run test:auth
```

O workflow `.github/workflows/auth-e2e.yml` provisiona PostgreSQL, backend e frontend reais e valida cookies HttpOnly, CSRF, refresh, logout e falha segura do gateway.

Os números de cobertura variam por commit e não são apresentados como garantia permanente. Veja [testes e qualidade](docs/10-testes/README.md) e [testes de telemedicina](docs/10-testes/telemedicina.md).

## Segurança e dados clínicos

O projeto contém controles de segurança, mas não deve ser considerado automaticamente pronto para produção. Entre os controles implementados estão:

- Argon2 como primeiro password hasher;
- JWT com rotação e blacklist de refresh tokens;
- cookies access/refresh `HttpOnly`, `Secure` em produção e `SameSite=Lax`;
- double-submit CSRF para operações mutáveis;
- respostas do gateway BFF sanitizadas, sem URL, causa ou stack interna;
- bloqueio de conta após tentativas falhas;
- campos clínicos textuais criptografados antes da persistência;
- regras específicas para evoluções confidenciais;
- validação de extensão, MIME e assinatura de uploads clínicos;
- auditoria de ações sensíveis;
- destinos de comunicação criptografados e mascarados;
- tokens públicos persistidos somente como hash, com expiração e revogação;
- JWTs LiveKit de curta duração sem dados pessoais em identidade ou metadata;
- chave E2EE individual por sala, criptografada em repouso e mantida apenas em memória no navegador;
- webhook LiveKit assinado e idempotente;
- ausência deliberada de gravação, transcrição, chat persistente e compartilhamento de tela;
- validação de segredos e headers de segurança no ambiente de produção.

Antes de armazenar dados reais, configure HTTPS, segredos independentes, PostgreSQL gerenciado, Redis, storage privado persistente, backup/restauração, monitoramento, alertas, e-mail e tokens de webhook. Cookies HttpOnly reduzem exfiltração de JWT por XSS, mas não eliminam ações em nome do usuário; CSP e sanitização continuam obrigatórias.

Leia o [guia de segurança](docs/08-seguranca/README.md), a [segurança da telemedicina](docs/08-seguranca/telemedicina.md), a [autenticação da API](docs/07-api/autenticacao.md), o [mapeamento técnico de LGPD](docs/09-lgpd/README.md) e a [documentação de Comunicações](docs/05-modulos/comunicacoes/README.md).

## Estrutura do projeto

```text
EloTerapeutico/
├── backend/                 # Django REST API, Celery e backoffice
├── frontend/                # Next.js App Router, BFF e E2E
├── docs/                    # Portal técnico e operacional
├── docker-compose.yml       # Ambiente local
├── AGENTS.md                # Regras para agentes e colaboradores
└── README.md
```

## Documentação

O portal principal está em [`docs/README.md`](docs/README.md). Referências importantes:

- [telemedicina](docs/05-modulos/telemedicina/README.md);
- [API de telemedicina](docs/07-api/endpoints/telemedicina.md);
- [operação de telemedicina](docs/12-operacao/telemedicina.md);
- [status do projeto](docs/17-referencia/status-do-projeto.md);
- [matriz de módulos](docs/17-referencia/matriz-de-modulos.md);
- [matriz de integrações](docs/17-referencia/matriz-de-integracoes.md);
- [auditoria do backlog](docs/17-referencia/auditoria-backlog.md);
- [roadmap](docs/IMPLEMENTATION_ROADMAP.md);
- [limitações conhecidas](docs/01-visao-geral/limitacoes.md);
- [arquitetura do backend](docs/architecture/backend-architecture-map.md);
- [cookies, headers e storage](docs/08-seguranca/headers-cookies-storage.md).

## Contribuição

Não altere diretamente a `main`. Use uma branch específica, commits pequenos em português e Pull Request. Antes de enviar, execute os checks relevantes e verifique migrations.

Consulte [como contribuir](docs/14-contribuicao/README.md).

## Limitações conhecidas

- o isolamento multi-tenant de módulos legados ainda precisa de validação transversal;
- a telemedicina depende de credenciais LiveKit, HTTPS/WSS, webhook e smoke test em staging;
- o portal do paciente não está implementado como domínio completo;
- IA não possui integração funcional;
- storage privado e persistente depende de configuração operacional;
- e-mail, WhatsApp Business e SMS dependem de provedores oficiais;
- Asaas depende de credenciais, webhook e validação em staging;
- a cobertura frontend ainda é menor que a backend;
- backup, restauração e observabilidade dependem do ambiente de implantação.

Veja a lista completa em [limitações](docs/01-visao-geral/limitacoes.md).

## Licenciamento

O repositório não contém um arquivo `LICENSE` na revisão documentada. Não presuma permissão de redistribuição ou uso comercial sem autorização do mantenedor.

## Mantenedor

Repositório mantido por [FlavioProgramador](https://github.com/FlavioProgramador).
