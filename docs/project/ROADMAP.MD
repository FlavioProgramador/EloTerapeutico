# Roadmap Completo: Sistema de Gestão para Terapeutas

Este roadmap foi estruturado especificamente para o desenvolvimento de um **Sistema de Gestão para Terapeutas (SaaS)** utilizando **Django (Backend)**, **Next.js (Frontend)** e implantação na **Azure para Estudantes**.

Como se trata de um sistema que lida com dados de saúde (prontuários, evoluções clínicas, históricos de pacientes), o projeto deve seguir rigidamente os pilares de segurança da **LGPD (Lei Geral de Proteção de Dados)** desde o primeiro dia.

---

## 🛠️ Stack Tecnológica & Infraestrutura

* **Backend:** Django 5.x + Django Rest Framework (DRF) + SimpleJWT (Autenticação)
* **Frontend:** Next.js 14+ (App Router) + Tailwind CSS + Shadcn UI / Radix UI
* **Banco de Dados:** PostgreSQL (Produção) / SQLite (Desenvolvimento local)
* **Infraestrutura (Azure for Students):**
    * **Azure App Service:** Hospedagem do Backend (Django) e Frontend (Next.js) usando os planos gratuitos (F1/B1 Free).
    * **Azure Database for PostgreSQL:** Camada gratuita (Flexible Server - se disponível nos créditos) ou hospedado em uma máquina virtual Linux B1s (gratuita por 12 meses).
    * **Azure Blob Storage:** Armazenamento seguro de documentos e arquivos de prontuários (anexos).

---

## 🗺️ Fase 1: Concepção, Arquitetura e LGPD
**Objetivo:** Definir o escopo, modelagem de dados e garantir a conformidade legal antes de escrever o primeiro bloco de código.

### 1.1 Módulos do Sistema
* **Autenticação e Níveis de Acesso:** Cadastro de terapeutas, administradores de clínicas e secretárias.
* **Gestão de Pacientes (CRM):** Prontuário eletrônico, histórico médico, anamnese e evolução clínica.
* **Agenda Inteligente:** Marcação de consultas, recorrências, bloqueio de horários e status (Confirmado, Faltou, Cancelado).
* **Faturamento e Financeiro:** Controle de sessões pagas, pacotes de consultas, fluxo de caixa simples e emissão de recibos.
* **Notificações:** Lembretes de consultas via WhatsApp (Integração API) ou E-mail.

### 1.2 Modelagem de Dados (Entidades Principais)
* `User` (Custom User do Django para Terapeutas/Staff)
* `Patient` (Dados pessoais, contato, responsável legal se menor)
* `Appointment` (Data, hora, status, observações, vínculo com Terapeuta e Paciente)
* `MedicalRecord` / `Evolution` (Texto criptografado da sessão, CID-10 associado, data de criação e assinatura digital)
* `FinancialTransaction` (Valor, tipo: entrada/saída, status do pagamento, método)

### 1.3 Engenharia de Segurança (LGPD)
* **Criptografia em repouso:** Campos sensíveis do prontuário (`Evolution`) devem ser criptografados no banco de dados (ex: utilizando `django-cryptography`).
* **Logs de Acesso (Audit Trail):** Registrar quem visualizou ou editou o prontuário de um paciente e quando.
* **Anonimização:** Mecanismo para exclusão/anonimização de dados caso o paciente solicite (Direito de Esquecimento).

---

## 🐍 Fase 2: Desenvolvimento do Backend (Django)
**Objetivo:** Construir uma API REST robusta, segura e escalável.

### Passo 1: Setup Inicial
* Configurar o ambiente virtual (`venv` ou `poetry`).
* Configurar o projeto Django com separação de ambientes (`settings/dev.py` e `settings/prod.py`).
* Configurar suporte ao PostgreSQL.

### Passo 2: Autenticação Segura
* Implementar `django-rest-framework-simplejwt`.
* Criar endpoints para `/api/auth/register/`, `/api/auth/login/`, `/api/auth/refresh/`.
* Garantir que as senhas usei Argon2 ou BCrypt (configurável no Django).

### Passo 3: Desenvolvimento dos Apps Django
* **`apps.users`:** Gerenciamento do perfil do terapeuta, horários de atendimento, especialidades.
* **`apps.patients`:** CRUD de pacientes com validação de CPF e dados de contato.
* **`apps.records`:** Endpoints para Evolução Clínica. *Regra de negócio: Após 48h, a evolução não pode mais ser editada, apenas retificada por um termo aditivo (padrão CFM/CRP).*
* **`apps.agenda`:** Lógica de agendamento que impede choque de horários para o mesmo terapeuta.
* **`apps.financeiro`:** Registro de pagamentos por sessão.

### Passo 4: Documentação da API
* Configurar `drf-spectacular` ou `drf-yasg` para gerar a documentação Swagger/OpenAPI automaticamente em `/api/docs/`.

---

## ⚛️ Fase 3: Desenvolvimento do Frontend (Next.js)
**Objetivo:** Criar uma interface fluida, rápida e com excelente usabilidade para o terapeuta usar entre as sessões.

### Passo 1: Estrutura do Projeto
* Instanciar o Next.js com TypeScript, Tailwind CSS e App Router (`src/app`).
* Configurar a estrutura de pastas: `components/ui`, `hooks`, `services`, `types`, `context`.

### Passo 2: Autenticação e Middleware
* Implementar gerenciamento de sessão (armazenamento do JWT em HttpOnly cookies via Next.js Server Actions ou utilizando `next-auth`).
* Criar um `middleware.ts` para proteger rotas internas (`/dashboard/*`, `/pacientes/*`, `/agenda/*`).

### Passo 3: Construção das Telas da Aplicação
* **Layout Base:** Sidebar de navegação responsiva, cabeçalho com perfil do usuário e notificações.
* **Dashboard principal:** Cards com faturamento do mês, consultas no dia de hoje, e atalhos rápidos (Novo Paciente, Iniciar Consulta).
* **Módulo Agenda:** Integração com uma biblioteca de calendário (como `@fullcalendar/react` ou construir um grid nativo com Tailwind) para visualização diária/semanal.
* **Módulo Pacientes & Prontuário:**
    * Listagem com busca em tempo real.
    * Página de detalhes do paciente com linha do tempo (Timeline) das evoluções passadas.
    * Editor de texto rico (Rich Text) simples para digitação da evolução atual do paciente.

---

## ☁️ Fase 4: Integração com a Azure (Camada Gratuita)
**Objetivo:** Publicar a aplicação na nuvem utilizando os benefícios do plano de estudante da Azure.

### 4.1 Estratégia de Arquitetura na Azure
Como os planos gratuitos possuem limitações, utilizaremos a seguinte divisão:
1.  **Backend (API Django):** Azure App Service no plano gratuito Linux (F1).
2.  **Frontend (Next.js):** Pode ser hospedado no Azure Static Web Apps (gratuito para projetos pessoais/estudantes) se exportado como estático, ou no Azure App Service se precisar do SSR (Server-Side Rendering). Para simplificar o uso do App Router com chamadas dinâmicas, o Azure App Service (F1) com Node.js é o ideal.
3.  **Banco de Dados:** Criar uma Máquina Virtual Linux Ubuntu (B1s - inclusa na lista de serviços gratuitos por 12 meses da Azure). Dentro dela, instalar o PostgreSQL manualmente para economizar os créditos mensais da Azure.
4.  **Arquivos Físicos:** Criar uma conta de Azure Blob Storage (ZRS/LRS Hot) para salvar PDFs gerados ou anexos enviados pelos terapeutas.

### 4.2 Passos de Configuração
* **Configuração de Variáveis de Ambiente:** Utilizar a aba *Configuration -> Application Settings* do Azure App Service para injetar as chaves secretas (`SECRET_KEY`, `DATABASE_URL`, `AZURE_STORAGE_CONNECTION_STRING`) de forma segura, nunca deixando-as expostas no GitHub.
* **Configuração do Gunicorn/Uvicorn:** No Django, configurar o comando de inicialização na Azure para rodar as migrações e iniciar o servidor web:
    ```bash
    python manage.py migrate && gunicorn --bind=0.0.0.0:8000 meu_projeto.wsgi
    ```

---

## 🔄 Fase 5: CI/CD e Automação
**Objetivo:** Automatizar o processo de deploy para que cada commit no branch `main` atualize o sistema automaticamente.

* **GitHub Actions:** Criar dois workflows separados no repositório:
    * `.github/workflows/deploy-backend.yml`: Roda os testes unitários do Django, faz o build da imagem ou do pacote e envia para o Azure App Service via Azure Web Apps Deploy Action.
    * `.github/workflows/deploy-frontend.yml`: Valida o build do Next.js e faz o deploy no App Service correspondente.

---

## 🚀 Cronograma Sugerido de Implementação (Sprints)

| Sprint | Duração | Foco Principal | Entregáveis |
| :--- | :--- | :--- | :--- |
| **Sprint 1** | 1 Semana | Setup & Autenticação | Repositórios configurados, Banco de dados conectado, Login/Cadastro funcionando no Back e Front. |
| **Sprint 2** | 2 Semanas | Módulo de Pacientes & LGPD | CRUD de pacientes, Prontuário Eletrônico com criptografia ativa, Timeline de Evoluções prontas no Front. |
| **Sprint 3** | 2 Semanas | Agenda & Calendário | Grid de horários funcionando, criação, arrastar/soltar consultas, validações de choque de horários. |
| **Sprint 4** | 1 Semana | Financeiro & Relatórios | Fluxo de caixa básico, marcação de consultas pagas, geração de recibos em PDF. |
| **Sprint 5** | 1 Semana | Deploy Azure & Testes | Configuração da infraestrutura Azure, deploy contínuo ativo, testes de estresse na camada gratuita e homologação. |

---

## 💡 Dicas de Ouro para o Sucesso do Projeto
1.  **CORS Errors:** Lembre-se de configurar corretamente o `django-cors-headers` permitindo apenas a URL do seu domínio Next.js na nuvem em produção.
2.  **Cold Start da Azure (F1):** Planos gratuitos da Azure entram em "modo de suspensão" se passarem algum tempo sem acessos. O primeiro acesso do dia pode demorar de 20 a 30 segundos para carregar o backend. Não se assuste, isso é normal para a camada free. Para contornar, você pode criar um script simples de *ping* ou aceitar essa limitação na fase de desenvolvimento/validação.
3.  **Segurança dos Prontuários:** Nunca salve o texto do prontuário em texto limpo (Plain Text). Se a sua base de dados for comprometida, dados de saúde expostos geram multas altíssimas pela LGPD. Use criptografia simétrica no nível da aplicação (Django).