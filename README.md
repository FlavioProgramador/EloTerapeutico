# Elo Terapêutico — Plataforma de Gestão Clínica

> Prontuário eletrônico, agenda e controle financeiro para psicólogos e terapeutas. Conformidade com LGPD. Arquitetura SaaS multi-tenant.

---

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Git

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements/local.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Migrar banco de dados
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor de desenvolvimento
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local
# Edite .env.local com NEXT_PUBLIC_API_URL

# Iniciar servidor de desenvolvimento
npm run dev
```

Acesse em: http://localhost:3000

---

## 📁 Estrutura do Projeto

```
elo-terapeutico/
├── backend/                  # Django REST API
│   ├── apps/
│   │   ├── accounts/         # Autenticação e perfis de usuário
│   │   ├── agenda/           # Agendamento de consultas
│   │   ├── patients/         # Gerenciamento de pacientes (CRM)
│   │   ├── records/          # Prontuários e evoluções clínicas
│   │   └── financeiro/       # Controle financeiro
│   ├── config/               # Configurações Django (settings, urls, wsgi)
│   └── requirements/         # Dependências por ambiente
│
├── frontend/                 # Next.js App Router
│   └── src/
│       ├── app/              # Páginas (App Router)
│       ├── components/       # Design System (Button, Card, Input...)
│       ├── features/         # Módulos por domínio (patients, agenda...)
│       ├── providers/        # Providers raiz (QueryClient, Theme, Auth)
│       ├── contexts/         # Contextos React (Auth)
│       ├── lib/              # Utilitários (api, utils)
│       ├── types/            # Tipos TypeScript de domínio
│       └── constants/        # Query Keys, labels, rotas
│
└── docs/                     # Documentação técnica
    ├── FRONTEND.md           # Arquitetura do frontend
    ├── BACKEND.md            # Arquitetura do backend
    └── DESIGN_SYSTEM.md      # Design System e tokens
```

---

## 🏗️ Stack Técnica

### Backend
| Tecnologia | Versão | Propósito |
|---|---|---|
| Python | 3.11+ | Linguagem |
| Django | 5.x | Framework web |
| Django REST Framework | 3.15 | API REST |
| PostgreSQL | 15+ | Banco de dados |
| Azure Blob Storage | — | Arquivos e documentos |
| Fernet (cryptography) | — | Criptografia de campos sensíveis (LGPD) |
| Simple JWT | — | Autenticação JWT |

### Frontend
| Tecnologia | Versão | Propósito |
|---|---|---|
| Next.js | 15+ (App Router) | Framework |
| TypeScript | 5+ | Linguagem |
| Tailwind CSS | v4 | Estilização |
| TanStack Query | v5 | Cache e sync de dados |
| React Hook Form | — | Formulários |
| Zod | v4 | Validação de schemas |
| Sonner | — | Notificações toast |
| next-themes | — | Dark mode |
| Framer Motion | — | Animações |

---

## 🔒 Segurança e Compliance

- **LGPD**: Campos clínicos sensíveis criptografados em repouso com Fernet (AES-256-CBC)
- **JWT**: Access tokens de 30 minutos com refresh automático silencioso
- **RBAC**: Controle de acesso por role (therapist/secretary/admin) no middleware Next.js
- **CSRF**: Proteção nativa do Django para endpoints de formulário
- **HTTPS**: Obrigatório em produção via configurações HSTS

---

## 🌿 Git Flow

| Branch | Propósito |
|---|---|
| `main` | Código estável, pronto para produção |
| `refactor/setup-ecosystem` | Instalação e configuração do ecossistema (Fase 2-4) |
| `feature/*` | Novas funcionalidades |
| `fix/*` | Correções de bugs |

---

## 📚 Documentação

- [FRONTEND.md](./docs/FRONTEND.md) — Arquitetura e padrões do frontend
- [BACKEND.md](./docs/BACKEND.md) — Arquitetura e APIs do backend
- [DESIGN_SYSTEM.md](./docs/DESIGN_SYSTEM.md) — Tokens, componentes e guidelines

---

## 📄 Licença

Propriedade privada. Todos os direitos reservados.
