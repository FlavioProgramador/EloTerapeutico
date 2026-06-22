# 🐍 Roadmap Completo – Backend (Django + DRF)

Este roadmap cobre **todo o ciclo de desenvolvimento do backend** do Elo Terapêutico, desde o setup inicial até funcionalidades avançadas como relatórios, integrações externas e monitoramento em produção.

> **Stack:** Python 3.11 · Django 5.x · Django Rest Framework · PostgreSQL · SimpleJWT · django-cryptography · Gunicorn · Azure App Service

---

## 📋 Índice

1. [Fase 1 – Setup & Fundação](#fase-1--setup--fundação)
2. [Fase 2 – Autenticação & Controle de Acesso](#fase-2--autenticação--controle-de-acesso)
3. [Fase 3 – Módulo de Pacientes (CRM)](#fase-3--módulo-de-pacientes-crm)
4. [Fase 4 – Módulo de Prontuário Eletrônico](#fase-4--módulo-de-prontuário-eletrônico)
5. [Fase 5 – Módulo de Agenda](#fase-5--módulo-de-agenda)
6. [Fase 6 – Módulo Financeiro](#fase-6--módulo-financeiro)
7. [Fase 7 – Notificações & Integrações](#fase-7--notificações--integrações)
8. [Fase 8 – Segurança & LGPD](#fase-8--segurança--lgpd)
9. [Fase 9 – Testes & Qualidade](#fase-9--testes--qualidade)
10. [Fase 10 – Deploy & Produção na Azure](#fase-10--deploy--produção-na-azure)
11. [Fase 11 – Monitoramento & Manutenção](#fase-11--monitoramento--manutenção)

---

## Fase 1 – Setup & Fundação

**Objetivo:** Estruturar o projeto Django com boas práticas desde o início, separando ambientes e garantindo um fluxo de trabalho saudável.

### 1.1 Estrutura de Pastas
```
backend/
├── elo_terapeutico/        # Configurações centrais do projeto
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py         # Configurações comuns
│   │   ├── dev.py          # Configurações de desenvolvimento
│   │   └── prod.py         # Configurações de produção
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/              # Usuários e perfis de terapeutas
│   ├── patients/           # Pacientes e anamneses
│   ├── records/            # Prontuário eletrônico e evoluções
│   ├── agenda/             # Agendamentos e horários
│   ├── financeiro/         # Pagamentos e fluxo de caixa
│   └── notifications/      # Notificações e alertas
├── core/                   # Utilitários, classes base e mixins
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── manage.py
└── Dockerfile
```

### 1.2 Tarefas
- [ ] Criar projeto Django com `django-admin startproject elo_terapeutico`
- [ ] Separar `settings/` em `base.py`, `dev.py` e `prod.py`
- [ ] Criar `CustomUser` model herdando de `AbstractBaseUser`
- [ ] Configurar PostgreSQL como banco de dados padrão
- [ ] Configurar variáveis de ambiente via `python-decouple` ou `django-environ`
- [ ] Configurar `CORS` com `django-cors-headers`
- [ ] Configurar `requirements/` separados por ambiente
- [ ] Configurar `pre-commit` com `black`, `isort` e `flake8`
- [ ] Configurar `pytest-django` como runner de testes
- [ ] Inicializar migrações base

---

## Fase 2 – Autenticação & Controle de Acesso

**Objetivo:** Implementar autenticação segura baseada em JWT e um sistema de permissões por papel (RBAC).

### 2.1 Modelo de Usuário Customizado (`apps/users`)

```python
# Papéis disponíveis no sistema
class UserRole(models.TextChoices):
    ADMIN      = 'admin',      'Administrador da Clínica'
    THERAPIST  = 'therapist',  'Terapeuta'
    SECRETARY  = 'secretary',  'Secretária'
```

### 2.2 Endpoints de Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/auth/register/` | Cadastro de novo terapeuta |
| `POST` | `/api/auth/login/` | Login e geração de tokens JWT |
| `POST` | `/api/auth/token/refresh/` | Renovação do access token |
| `POST` | `/api/auth/logout/` | Revogação do refresh token |
| `POST` | `/api/auth/password/change/` | Alteração de senha autenticado |
| `POST` | `/api/auth/password/reset/` | Solicitação de reset de senha por e-mail |
| `GET`  | `/api/auth/me/` | Dados do usuário autenticado |

### 2.3 Tarefas
- [ ] Implementar `CustomUser` com campos: `role`, `crp_number`, `specialty`, `phone`, `avatar`
- [ ] Configurar `SimpleJWT` com tokens de curta duração (access: 30min, refresh: 7 dias)
- [ ] Implementar `IsTherapist`, `IsAdmin`, `IsSecretary` como permission classes do DRF
- [ ] Armazenar tokens JWT em cookies `HttpOnly` + `Secure` via middleware
- [ ] Implementar serializer de registro com validação de CPF e CRP
- [ ] Implementar endpoint de perfil do terapeuta (`/api/users/profile/`)
- [ ] Configurar `Argon2` como hasher de senha padrão
- [ ] Implementar bloqueio de conta após 5 tentativas de login falhas
- [ ] Criar testes unitários para todos os endpoints de autenticação

---

## Fase 3 – Módulo de Pacientes (CRM)

**Objetivo:** CRUD completo de pacientes com validações, busca eficiente e histórico de relacionamento.

### 3.1 Modelo `Patient`

```python
class Patient(models.Model):
    # Dados Pessoais
    full_name       = models.CharField(max_length=255)
    cpf             = models.CharField(max_length=14, unique=True)
    birth_date      = models.DateField()
    gender          = models.CharField(max_length=20, choices=GenderChoices)
    
    # Contato
    email           = models.EmailField(blank=True)
    phone           = models.CharField(max_length=20)
    
    # Endereço
    address         = models.JSONField(default=dict)  # CEP, rua, cidade, estado
    
    # Relacionamento terapêutico
    therapist       = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    status          = models.CharField(choices=PatientStatus)  # ativo, inativo, alta
    referral_source = models.CharField(max_length=100, blank=True)
    
    # Responsável legal (menores)
    guardian_name   = models.CharField(max_length=255, blank=True)
    guardian_cpf    = models.CharField(max_length=14, blank=True)
    
    # Controle
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    is_active       = models.BooleanField(default=True)
```

### 3.2 Endpoints de Pacientes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/patients/` | Listagem paginada com busca e filtros |
| `POST` | `/api/patients/` | Cadastrar novo paciente |
| `GET` | `/api/patients/{id}/` | Detalhes de um paciente |
| `PATCH` | `/api/patients/{id}/` | Atualização parcial de dados |
| `DELETE` | `/api/patients/{id}/` | Desativação (soft delete) |
| `GET` | `/api/patients/{id}/summary/` | Resumo clínico completo do paciente |
| `GET` | `/api/patients/{id}/appointments/` | Histórico de consultas |
| `GET` | `/api/patients/{id}/documents/` | Documentos e anexos do paciente |
| `POST` | `/api/patients/{id}/documents/` | Upload de documento do paciente |

### 3.3 Tarefas
- [ ] Criar model `Patient` com todos os campos listados
- [ ] Implementar validação de CPF (algoritmo verificador de dígitos)
- [ ] Implementar `soft delete` (campo `is_active` e `deleted_at`)
- [ ] Configurar busca em tempo real por nome, CPF e telefone (`SearchFilter`)
- [ ] Implementar filtros por status, terapeuta e data de cadastro
- [ ] Implementar paginação customizada (20 por página)
- [ ] Garantir que o terapeuta só veja os próprios pacientes (`queryset` filtrado por `request.user`)
- [ ] Implementar upload de documentos (PDF, imagem) para Azure Blob Storage
- [ ] Criar testes para validação de CPF, permissões e filtros

---

## Fase 4 – Módulo de Prontuário Eletrônico

**Objetivo:** Sistema seguro de registro de evoluções clínicas com criptografia, imutabilidade e conformidade com CRP/CFM.

### 4.1 Modelos

```python
class Anamnesis(models.Model):
    """Ficha de anamnese inicial do paciente – preenchida na primeira sessão."""
    patient         = models.OneToOneField(Patient, on_delete=models.PROTECT)
    chief_complaint = EncryptedTextField()      # Queixa principal (criptografado)
    history         = EncryptedTextField()      # Histórico (criptografado)
    medications     = EncryptedTextField()      # Medicações em uso
    family_history  = EncryptedTextField()
    created_at      = models.DateTimeField(auto_now_add=True)
    created_by      = models.ForeignKey(CustomUser, on_delete=models.PROTECT)

class Evolution(models.Model):
    """Evolução clínica de uma sessão – imutável após 48h."""
    patient         = models.ForeignKey(Patient, on_delete=models.PROTECT)
    appointment     = models.OneToOneField('agenda.Appointment', on_delete=models.SET_NULL, null=True)
    content         = EncryptedTextField()      # Texto da sessão (criptografado)
    cid10           = models.CharField(max_length=10, blank=True)
    session_date    = models.DateField()
    is_locked       = models.BooleanField(default=False)
    locked_at       = models.DateTimeField(null=True, blank=True)
    created_by      = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

class EvolutionAddendum(models.Model):
    """Termo aditivo para correções após o período de 48h."""
    evolution       = models.ForeignKey(Evolution, on_delete=models.PROTECT, related_name='addenda')
    reason          = models.TextField()
    content         = EncryptedTextField()
    created_by      = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at      = models.DateTimeField(auto_now_add=True)
```

### 4.2 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET/POST` | `/api/patients/{id}/anamnesis/` | Leitura e criação da anamnese |
| `PATCH` | `/api/patients/{id}/anamnesis/` | Atualização da anamnese |
| `GET` | `/api/patients/{id}/evolutions/` | Listagem cronológica de evoluções |
| `POST` | `/api/patients/{id}/evolutions/` | Criar nova evolução |
| `GET` | `/api/evolutions/{id}/` | Detalhe de uma evolução |
| `PATCH` | `/api/evolutions/{id}/` | Editar evolução (apenas dentro de 48h) |
| `POST` | `/api/evolutions/{id}/addendum/` | Criar termo aditivo (após 48h) |
| `POST` | `/api/evolutions/{id}/export/` | Exportar evolução como PDF |

### 4.3 Tarefas
- [ ] Instalar e configurar `django-cryptography`; definir `FIELD_ENCRYPTION_KEY` via env
- [ ] Criar `EncryptedTextField` como campo customizado
- [ ] Implementar tarefa agendada (via `celery` ou `management command`) para bloquear evoluções após 48h
- [ ] Criar serializer que recuse edição em evoluções com `is_locked=True`
- [ ] Implementar `EvolutionAddendum` para retificações pós-bloqueio
- [ ] Implementar geração de PDF com `reportlab` ou `weasyprint`
- [ ] Criar signal para registrar log de auditoria em cada leitura de evolução
- [ ] Garantir que somente o terapeuta responsável pelo paciente acesse o prontuário

---

## Fase 5 – Módulo de Agenda

**Objetivo:** Sistema de agendamento inteligente com detecção de conflitos, recorrências e múltiplos status de consulta.

### 5.1 Modelos

```python
class WorkingHours(models.Model):
    """Horários de atendimento configuráveis por terapeuta."""
    therapist   = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    weekday     = models.IntegerField(choices=Weekday)  # 0=Seg ... 6=Dom
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    is_active   = models.BooleanField(default=True)

class Appointment(models.Model):
    """Consulta agendada."""
    patient     = models.ForeignKey(Patient, on_delete=models.PROTECT)
    therapist   = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    start_time  = models.DateTimeField()
    end_time    = models.DateTimeField()
    duration    = models.PositiveIntegerField(default=50)  # em minutos
    status      = models.CharField(choices=AppointmentStatus)
    # Confirmado | Aguardando | Faltou | Cancelado | Remarcado
    notes       = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)  # RRULE
    session_value = models.DecimalField(max_digits=8, decimal_places=2)
    created_at  = models.DateTimeField(auto_now_add=True)
```

### 5.2 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/agenda/` | Listar consultas por período (query params: `start`, `end`) |
| `POST` | `/api/agenda/` | Criar nova consulta |
| `GET` | `/api/agenda/{id}/` | Detalhe de uma consulta |
| `PATCH` | `/api/agenda/{id}/` | Atualizar status ou dados da consulta |
| `DELETE` | `/api/agenda/{id}/` | Cancelar/remover consulta |
| `GET` | `/api/agenda/today/` | Consultas do dia atual |
| `GET` | `/api/users/working-hours/` | Horários de atendimento do terapeuta |
| `PUT` | `/api/users/working-hours/` | Atualizar horários de atendimento |
| `POST` | `/api/agenda/check-availability/` | Verificar disponibilidade de horário |

### 5.3 Tarefas
- [ ] Criar model `WorkingHours` e `Appointment`
- [ ] Implementar validação de conflito de horários (query pelo intervalo `start_time` e `end_time`)
- [ ] Implementar recorrência de consultas (semanal/quinzenal/mensal) via `RRULE`
- [ ] Criar endpoint `/check-availability/` para o frontend verificar antes de abrir o seletor de horários
- [ ] Implementar filtro de consultas por período de datas
- [ ] Adicionar signal para criar `FinancialTransaction` quando status mudar para `Confirmado`
- [ ] Implementar cancelamento com motivo (campo `cancellation_reason`)
- [ ] Criar testes para detecção de conflito de horários e criação de recorrências

---

## Fase 6 – Módulo Financeiro

**Objetivo:** Controle de fluxo de caixa simples, vinculado às sessões, com geração de recibos.

### 6.1 Modelos

```python
class FinancialTransaction(models.Model):
    """Registro de cada transação financeira."""
    therapist       = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    patient         = models.ForeignKey(Patient, on_delete=models.PROTECT, null=True)
    appointment     = models.ForeignKey('agenda.Appointment', null=True, on_delete=models.SET_NULL)
    type            = models.CharField(choices=TransactionType)  # entrada | saída
    category        = models.CharField(choices=Category)         # sessão | assinatura | material | outro
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method  = models.CharField(choices=PaymentMethod)    # pix | cartão | dinheiro | transferência
    payment_status  = models.CharField(choices=PaymentStatus)    # pago | pendente | cancelado
    due_date        = models.DateField(null=True)
    paid_at         = models.DateTimeField(null=True)
    description     = models.TextField(blank=True)
    receipt_url     = models.URLField(blank=True)  # link do recibo no Blob Storage
    created_at      = models.DateTimeField(auto_now_add=True)
```

### 6.2 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/financeiro/` | Listagem de transações com filtros |
| `POST` | `/api/financeiro/` | Registrar nova transação manual |
| `PATCH` | `/api/financeiro/{id}/` | Marcar como pago ou atualizar dados |
| `GET` | `/api/financeiro/summary/` | Resumo do mês (entradas, saídas, saldo) |
| `GET` | `/api/financeiro/report/` | Relatório por período (query params: `start`, `end`) |
| `POST` | `/api/financeiro/{id}/receipt/` | Gerar e salvar recibo em PDF |
| `GET` | `/api/financeiro/pending/` | Listar sessões com pagamento pendente |

### 6.3 Tarefas
- [ ] Criar model `FinancialTransaction`
- [ ] Implementar signal em `Appointment` para criar transação automaticamente ao confirmar sessão
- [ ] Implementar endpoint `/summary/` com totais de entradas, saídas e saldo do período
- [ ] Implementar geração de recibo em PDF (dados do terapeuta, paciente, valor, data, método de pagamento)
- [ ] Fazer upload do PDF gerado para o Azure Blob Storage e salvar URL no model
- [ ] Criar testes para criação automática de transação via signal e cálculo do sumário

---

## Fase 7 – Notificações & Integrações

**Objetivo:** Enviar lembretes automáticos de consultas por e-mail e WhatsApp.

### 7.1 E-mail (SMTP / Azure Communication Services)

- [ ] Configurar backend de e-mail (`EMAIL_BACKEND`) com SMTP ou Azure Communication Services
- [ ] Criar template HTML de e-mail para lembrete de consulta
- [ ] Criar template HTML para confirmação de agendamento
- [ ] Criar template de e-mail para reset de senha
- [ ] Implementar `celery-beat` para envio automático de lembretes 24h antes da consulta

### 7.2 WhatsApp (Twilio ou Evolution API)

- [ ] Integrar API de WhatsApp (Twilio Sandbox ou Evolution API open-source)
- [ ] Criar serviço `WhatsAppService` com método `send_reminder(appointment)`
- [ ] Implementar fallback: se WhatsApp falhar, enviar e-mail
- [ ] Criar model `NotificationLog` para rastrear envios (status, canal, timestamp)
- [ ] Criar endpoint `POST /api/notifications/send-reminder/{appointment_id}/` para envio manual

### 7.3 Tarefas Agendadas (Celery + Redis)

| Tarefa | Frequência | Descrição |
|--------|-----------|-----------|
| `send_appointment_reminders` | Diária às 08:00 | Lembretes das consultas do próximo dia |
| `lock_old_evolutions` | Diária à meia-noite | Bloquear evoluções com mais de 48h |
| `generate_monthly_report` | 1º de cada mês | Gerar relatório financeiro mensal |

---

## Fase 8 – Segurança & LGPD

**Objetivo:** Garantir que o sistema esteja em plena conformidade com a LGPD e hardened contra ataques comuns.

### 8.1 Medidas Técnicas de Segurança

- [ ] Habilitar `SECURE_SSL_REDIRECT`, `HSTS`, `X_FRAME_OPTIONS`, `SECURE_CONTENT_TYPE_NOSNIFF` em `prod.py`
- [ ] Implementar rate limiting nos endpoints de autenticação (`django-ratelimit`)
- [ ] Configurar `CORS_ALLOWED_ORIGINS` apenas para o domínio do frontend em produção
- [ ] Habilitar `CSRF_COOKIE_SECURE` e `SESSION_COOKIE_SECURE`
- [ ] Implementar sanitização de inputs para prevenção de XSS e SQL Injection
- [ ] Criar `SecurityHeadersMiddleware` customizado

### 8.2 Trilha de Auditoria

- [ ] Criar model `AuditLog` com campos: `user`, `action`, `resource_type`, `resource_id`, `ip_address`, `timestamp`
- [ ] Criar `AuditLogMixin` para ViewSets que automaticamente registra `GET`, `POST`, `PATCH` em dados sensíveis
- [ ] Aplicar o mixin nos ViewSets de `Evolution` e `Anamnesis`
- [ ] Endpoint `GET /api/audit-logs/` (somente Admin) para consultar logs

### 8.3 Direitos LGPD

- [ ] Endpoint `POST /api/patients/{id}/export-data/` – exporta todos os dados do paciente como JSON/ZIP
- [ ] Endpoint `DELETE /api/patients/{id}/anonymize/` – anonimiza dados pessoais (mantém financeiro)
- [ ] Endpoint `GET /api/patients/{id}/consent/` – exibe histórico de consentimentos

---

## Fase 9 – Testes & Qualidade

**Objetivo:** Garantir cobertura de testes acima de 80% e CI bloqueando merges com falhas.

### 9.1 Estratégia de Testes

| Tipo | Ferramenta | Foco |
|------|-----------|------|
| Unitários | `pytest-django` + `factory_boy` | Models, serializers, serviços, utilitários |
| Integração | `pytest-django` + `APIClient` | Endpoints REST, fluxos completos |
| Segurança | `pytest` | Testes de permissão (usuário A não acessa dados do usuário B) |
| Criptografia | `pytest` | Garantir que `Evolution.content` nunca é salvo em texto puro |

### 9.2 Tarefas

- [ ] Configurar `pytest.ini` ou `pyproject.toml` com settings de teste
- [ ] Criar `conftest.py` global com fixtures: `api_client`, `therapist_user`, `patient`, `appointment`
- [ ] Atingir **80%+ de cobertura** (verificar com `pytest --cov=apps`)
- [ ] Configurar `factory_boy` para todos os models principais
- [ ] Adicionar testes de permissão (RBAC): garantir que `Secretary` não acesse evoluções
- [ ] Configurar GitHub Actions para rodar `pytest` em todo PR

---

## Fase 10 – Deploy & Produção na Azure

**Objetivo:** Publicar o backend na Azure App Service com deploy automatizado e zero downtime.

### 10.1 Configurações de Produção (`settings/prod.py`)

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` via variável de ambiente
- [ ] Banco de dados PostgreSQL via `DATABASE_URL` (Azure Flexible Server ou VM B1s)
- [ ] `STATIC_ROOT` + `STATICFILES_STORAGE` configurado para servir via WhiteNoise ou Azure CDN
- [ ] `DEFAULT_FILE_STORAGE` configurado para Azure Blob Storage
- [ ] Logging estruturado em JSON para Azure Monitor

### 10.2 Tarefas

- [ ] Criar `prod.py` completo com todas as variáveis de ambiente
- [ ] Configurar `gunicorn` com workers e timeout adequados
- [ ] Criar script de startup (`startup.sh`) com: `migrate`, `collectstatic` e `gunicorn`
- [ ] Configurar Azure App Service para usar Python 3.11
- [ ] Definir todas as variáveis secretas em **Azure App Service > Configuration > Application Settings**
- [ ] Criar workflow `.github/workflows/deploy-backend.yml` (testes → build → deploy na Azure)
- [ ] Configurar health check endpoint `GET /api/health/` para o Azure monitorar

### 10.3 GitHub Actions – Deploy Backend

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend
on:
  push:
    branches: [main]
    paths: ['backend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install dependencies
        run: pip install -r requirements/dev.txt
      - name: Run tests
        run: pytest --cov=apps --cov-fail-under=80

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ secrets.AZURE_BACKEND_APP_NAME }}
          publish-profile: ${{ secrets.AZURE_BACKEND_PUBLISH_PROFILE }}
```

---

## Fase 11 – Monitoramento & Manutenção

**Objetivo:** Garantir visibilidade do sistema em produção e reagir rápido a incidentes.

### 11.1 Tarefas

- [ ] Integrar **Azure Application Insights** para rastreamento de erros e performance
- [ ] Configurar logging estruturado (`structlog`) com envio para Azure Monitor
- [ ] Implementar `GET /api/health/` retornando status do banco, cache e storage
- [ ] Configurar alertas de e-mail para erros 5xx no Azure Application Insights
- [ ] Documentar processo de rollback de deploy
- [ ] Configurar backups automáticos do PostgreSQL (Azure Backup ou pg_dump agendado)
- [ ] Criar `CHANGELOG.md` com versionamento semântico a cada release

---

## 🗓️ Cronograma Resumido

| Fase | Duração Estimada | Prioridade |
|------|:----------------:|:----------:|
| 1 – Setup & Fundação | 3 dias | 🔴 Alta |
| 2 – Autenticação & RBAC | 5 dias | 🔴 Alta |
| 3 – Módulo de Pacientes | 5 dias | 🔴 Alta |
| 4 – Prontuário Eletrônico | 7 dias | 🔴 Alta |
| 5 – Módulo de Agenda | 7 dias | 🔴 Alta |
| 6 – Módulo Financeiro | 5 dias | 🟡 Média |
| 7 – Notificações & Integrações | 5 dias | 🟡 Média |
| 8 – Segurança & LGPD | 4 dias | 🔴 Alta |
| 9 – Testes & Qualidade | Contínuo | 🔴 Alta |
| 10 – Deploy & Produção | 3 dias | 🔴 Alta |
| 11 – Monitoramento | 2 dias | 🟡 Média |

> 📌 **Total estimado:** ~46 dias úteis de desenvolvimento solo, considerando revisões e retrabalho.
