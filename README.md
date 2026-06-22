# Elo Terapêutico - Sistema de Gestão para Terapeutas (SaaS)

O **Elo Terapêutico** é uma plataforma SaaS (Software as a Service) desenvolvida para simplificar e assegurar a gestão de consultórios e clínicas de terapia. O sistema oferece prontuário eletrônico criptografado, agenda inteligente, controle financeiro e conformidade nativa com a **Lei Geral de Proteção de Dados (LGPD)**.

---

## 🛠️ Stack Tecnológica

### Backend
* **Django 5.x** & **Django Rest Framework (DRF)**
* **SimpleJWT** (Autenticação baseada em tokens JWT)
* **PostgreSQL** (Banco de dados relacional robusto)
* **django-cryptography** (Criptografia de dados de prontuário em nível de banco de dados)

### Frontend
* **Next.js 14+** (App Router & Server Actions)
* **Tailwind CSS** & **Shadcn UI** (Design system limpo, responsivo e moderno)
* **TypeScript** (Tipagem estática e maior segurança de código)

### Infraestrutura & DevOps
* **Azure App Service** (Hospedagem da API e do Frontend)
* **Azure Database/VM (PostgreSQL)** (Banco de dados principal)
* **Azure Blob Storage** (Armazenamento seguro de anexos e documentos)
* **GitHub Actions** (CI/CD automatizado)

---

## 🚀 Como Iniciar Localmente

O projeto está dividido em duas partes principais: `/backend` e `/frontend`.

### 1. Pré-requisitos
* Python 3.10 ou superior instalado.
* Node.js 18.x ou superior instalado.
* Banco de dados PostgreSQL rodando localmente (ou SQLite para desenvolvimento ágil).

---

### 2. Configurando o Backend (Django)

1. Navegue até o diretório do backend (crie a pasta caso esteja iniciando a estrutura):
   ```bash
   cd backend
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Copie as variáveis de ambiente de exemplo e configure seu arquivo `.env`:
   ```bash
   cp .env.example .env
   ```

5. Execute as migrações do banco de dados:
   ```bash
   python manage.py migrate
   ```

6. Inicie o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```
   *O backend estará acessível em: `http://127.0.0.1:8000/`*

---

### 3. Configurando o Frontend (Next.js)

1. Navegue até o diretório do frontend:
   ```bash
   cd frontend
   ```

2. Instale as dependências com o npm:
   ```bash
   npm install
   ```

3. Copie o arquivo de variáveis de ambiente de exemplo:
   ```bash
   cp .env.example .env.local
   ```

4. Execute o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```
   *O frontend estará acessível em: `http://localhost:3000/`*

---

## 🔒 Segurança e LGPD

Por lidar com dados de saúde (dados pessoais sensíveis), este projeto implementa práticas rigorosas de segurança:
* **Criptografia Simétrica:** Evoluções clínicas e notas de sessão são criptografadas antes de serem gravadas no banco de dados.
* **Logs de Auditoria:** Rastreabilidade total sobre quais usuários visualizaram ou modificaram prontuários específicos.
* **Consentimento e Anonimização:** Mecanismos preparados para exportação ou eliminação segura de dados sob demanda do paciente (Direito ao Esquecimento).

Para mais detalhes sobre as práticas de privacidade implementadas, consulte o documento [LGPD_COMPLIANCE.md](file:///d:/Projetos/elo-terapeutico/LGPD_COMPLIANCE.md).

---

## 🗺️ Roadmap de Desenvolvimento

O plano completo de desenvolvimento, incluindo cronogramas de sprints e estratégias de implantação gratuita na Azure, está detalhado no arquivo [ROADMAP.MD](file:///d:/Projetos/elo-terapeutico/ROADMAP.MD).
