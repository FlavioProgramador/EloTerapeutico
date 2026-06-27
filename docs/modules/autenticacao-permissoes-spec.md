# Especificação Técnica — Autenticação e Permissões

Este documento especifica o módulo de **Autenticação e Permissões (RBAC - Role‑Based Access Control)** do sistema **Elo Terapêutico**. Ele serve como guia para a implementação, testes e validação da segurança da plataforma.

---

## 1. Objetivo e Escopo

O objetivo do módulo é garantir o acesso seguro à plataforma Elo Terapêutico, identificando os usuários através de credenciais criptografadas, controlando suas sessões por meio de JSON Web Tokens (JWT) e aplicando regras de autorização conforme o papel (role) atribuído à conta.

### Em Escopo
*   **Cadastro (Registro):** Criação de novas contas com papéis específicos (`therapist`, `secretary`, `admin`).
*   **Autenticação (Login):** Login seguro com validação de senha (bcrypt/argon2) e retorno de par de tokens (Access e Refresh JWT).
*   **Controle de Sessão (Logout & Refresh):**
    *   Renovação silenciosa de tokens (silent refresh) no frontend.
    *   Invalidação de tokens no logout (blacklist de refresh token) e invalidação por alteração de senha.
*   **Políticas de Bloqueio (Lockout):** Bloqueio temporário da conta (30 minutos) após 5 tentativas consecutivas de login malsucedidas.
*   **Controle de Acesso Baseado em Papéis (RBAC):**
    *   Restrição de endpoints no backend por meio de classes de permissão do DRF.
    *   Proteção de rotas no Next.js via Middleware baseado no cookie da role.
*   **Redefinição de Senha (Forgot Password):** Envio de e-mail de recuperação de senha com token de validação de uso único e redefinição de senha segura.
*   **Perfil do Usuário:** Consulta (`/api/v1/auth/me/`) e edição de perfil profissional e pessoal do terapeuta autenticado.
*   **Horários de Atendimento:** CRUD dos horários configurados pelo terapeuta.

### Fora de Escopo (Gaps identificados a serem planejados no futuro)
*   **Confirmação de Conta:** Verificação de e-mail pós-cadastro.
*   **Autenticação Multifator (MFA):** Verificação em duas etapas via SMS ou autenticador (OTP).
*   **Histórico de Conexões:** Log de auditoria detalhado dos IPs e dispositivos que efetuaram login.

---

## 2. Permissões & RBAC (Role-Based Access Control)

### Papéis Disponíveis
1.  **Terapeuta (`therapist`):** O papel padrão e principal. Tem acesso total aos seus pacientes, agendas, prontuários e dados financeiros associados a ele.
2.  **Secretária (`secretary`):** Apoio administrativo. Pode visualizar a agenda e cadastrar pacientes, mas **nunca** tem acesso a prontuários clínicos, evoluções ou relatórios financeiros de faturamento.
3.  **Administrador (`admin`):** Administrador de uma clínica. Tem acesso a todos os painéis, incluindo gerenciamento de secretárias, dados financeiros consolidados da clínica e controle de permissões.

### Matriz de Acesso a Rotas no Frontend

| Rota / Path | Terapeuta (`therapist`) | Secretária (`secretary`) | Administrador (`admin`) | Comportamento se Negado |
| :--- | :---: | :---: | :---: | :--- |
| `/login` e `/register` | ❌ (Redireciona) | ❌ (Redireciona) | ❌ (Redireciona) | Redireciona para `/dashboard` se já autenticado |
| `/dashboard` (Home) | ✅ | ✅ | ✅ | Redireciona para `/login` |
| `/dashboard/patients` | ✅ | ✅ | ✅ | Redireciona para `/login` |
| `/dashboard/records` (Prontuários) | ✅ | ❌ | ✅ | Redireciona para `/dashboard?error=access_denied_records` |
| `/dashboard/agenda` | ✅ | ✅ | ✅ | Redireciona para `/login` |
| `/dashboard/financeiro` | ✅ | ❌ | ✅ | Redireciona para `/dashboard?error=access_denied_financeiro` |
| `/dashboard/admin` (Configurações) | ❌ | ❌ | ✅ | Redireciona para `/dashboard?error=access_denied_admin` |

### Multi-tenancy no Backend (Isolamento de Dados)
> [!IMPORTANT]
> A autorização no frontend é meramente estética e de navegação. O backend é o responsável final por aplicar o isolamento de dados.
*   **Toda consulta** a entidades como `Patient`, `Appointment`, `Record` ou `Transaction` deve ser restrita ao terapeuta associado ao registro.
*   Um terapeuta **nunca** poderá ler ou alterar dados pertencentes a outro terapeuta.
*   Classes de permissão DRF como `IsOwnerOrAdmin` validam no nível do objeto se `obj.therapist == request.user`.

---

## 3. Modelo de Dados

As tabelas de autenticação e configuração de perfil estão representadas abaixo:

### User (Custom User Model)
Herdado de `AbstractBaseUser` e `PermissionsMixin` do Django.

*   `id` (BigInt, PK): Identificador único.
*   `email` (EmailField, Unique, Index): Identificador de login do usuário.
*   `full_name` (CharField, max_length=255): Nome completo.
*   `role` (CharField, escolhas: `therapist`, `secretary`, `admin`, default `therapist`): Papel do usuário.
*   `specialty` (CharField, max_length=100, blank=True): Especialidade do profissional.
*   `crp_number` (CharField, max_length=20, blank=True): Registro profissional.
*   `bio` (TextField, blank=True): Apresentação textual do terapeuta.
*   `phone` (CharField, max_length=20, blank=True): Telefone para contato.
*   `avatar` (ImageField, upload_to="avatars/", null=True): Foto de perfil.
*   `default_session_duration` (PositiveIntegerField, default=50): Duração padrão das sessões em minutos.
*   `default_session_value` (DecimalField, max_digits=8, decimal_places=2, default=0.00): Valor padrão cobrado por sessão.
*   `is_active` (BooleanField, default=True): Indica se a conta está ativa.
*   `is_staff` (BooleanField, default=False): Acesso ao Django Admin.
*   `date_joined` (DateTimeField, default=timezone.now): Data de criação da conta.
*   `failed_login_attempts` (PositiveSmallIntegerField, default=0): Contador de tentativas falhas.
*   `locked_until` (DateTimeField, null=True): Timestamp até o qual a conta permanecerá bloqueada por falhas repetidas.

### WorkingHours
Configurações semanais de agenda do terapeuta.

*   `id` (BigInt, PK): Identificador único.
*   `therapist` (ForeignKey -> User, cascade): Terapeuta dono do horário.
*   `weekday` (IntegerField, escolhas: 0 a 6, Segunda a Domingo): Dia da semana.
*   `start_time` (TimeField): Hora de início do atendimento.
*   `end_time` (TimeField): Hora de término do atendimento.
*   `is_active` (BooleanField, default=True): Se o dia está disponível para agendamento.

---

## 4. Endpoints da API (Backend)

Todos os endpoints estão documentados no Swagger OpenAPI (`/api/docs/`).

| Método | Endpoint | Permissão | Descrição |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register/` | `AllowAny` | Registra uma nova conta de terapeuta e retorna os tokens JWT. |
| `POST` | `/api/v1/auth/login/` | `AllowAny` | Autentica e-mail/senha. Retorna tokens JWT. Processa lógica de bloqueio de conta. |
| `POST` | `/api/v1/auth/logout/` | `IsAuthenticated` | Coloca o `refresh_token` na blacklist no Django, invalidando a sessão. |
| `POST` | `/api/v1/auth/token/refresh/` | `AllowAny` | Recebe um `refresh` token e gera um novo `access` token. Rejeita tokens cujo claim `hash_password` não corresponda à senha atual (revogação nativa SimpleJWT). |
| `POST` | `/api/v1/auth/password/change/`| `IsAuthenticated` | Altera a senha do usuário logado, exigindo a senha atual. |
| `POST` | `/api/v1/auth/password/reset/`| `AllowAny` | Solicita link de reset de senha (resposta idêntica para e-mails existentes e inexistentes para mitigar enumeração de contas). |
| `POST` | `/api/v1/auth/password/reset/confirm/`| `AllowAny` | Confirma o reset de senha informando token, uidb64 e a nova senha. Invalida tokens JWT anteriores imediatamente. |
| `GET` | `/api/v1/auth/me/` | `IsAuthenticated` | Obtém informações detalhadas do perfil logado. |
| `PUT/PATCH`| `/api/v1/auth/me/` | `IsAuthenticated` | Atualiza dados cadastrais, especialidades e configurações padrões de sessão. |
| `GET` | `/api/v1/auth/working-hours/` | `IsAuthenticated` | Lista os horários de atendimento do usuário autenticado. |
| `POST` | `/api/v1/auth/working-hours/` | `IsTherapist` | Cadastra um novo horário de atendimento. |
| `PUT/PATCH`| `/api/v1/auth/working-hours/<id>/`| `IsOwnerOrAdmin` | Atualiza um horário de atendimento específico. |
| `DELETE` | `/api/v1/auth/working-hours/<id>/`| `IsOwnerOrAdmin` | Remove um horário de atendimento. |

---

## 5. Fluxos Principais e UX do Frontend

### A. Fluxo de Login
1.  O usuário preenche e-mail e senha.
2.  Zod valida os campos no cliente (e-mail válido, senha >= 8 caracteres).
3.  O botão de submissão entra em estado de `loading` (desabilitado).
4.  O serviço envia uma requisição `POST` para `/api/v1/auth/login/`.
5.  **Se bem-sucedido:**
    *   Os tokens `access` e `refresh` são gravados em cookies seguros (`auth_token` e `auth_refresh_token`).
    *   A role é gravada no cookie `auth_role` para uso no Next.js Middleware.
    *   O estado local de autenticação (`user` no `AuthContext`) é atualizado.
    *   O usuário é redirecionado para `/dashboard`.
6.  **Se malsucedido:**
    *   Retorna a mensagem de erro do servidor em um toast Sonner (`extractApiError`).
    *   Se for bloqueio de conta, exibe até qual horário a conta ficará inacessível.

### B. Renovação Silenciosa de Token (Silent Refresh)
Ocorre via interceptor do Axios (`frontend/src/lib/api.ts`):
1.  Uma requisição protegida falha com erro `HTTP 401 Unauthorized`.
2.  O interceptor detecta o erro e bloqueia a fila de chamadas pendentes (`failedQueue`).
3.  Envia uma chamada `POST` silenciosa para `/api/v1/auth/token/refresh/` passando o `auth_refresh_token` obtido via cookie.
4.  **Se a renovação funcionar:**
    *   Salva o novo `auth_token` e atualiza o cookie.
    *   Dispara as chamadas enfileiradas com o novo token Bearer.
5.  **Se falhar (refresh expirado ou invalidado por alteração de senha):**
    *   Limpa todos os cookies locais de sessão.
    *   Redireciona o usuário para `/login`.

### C. Fluxo de Redefinição de Senha (Forgot Password)
1.  O usuário solicita recuperação inserindo seu e-mail em `/forgot-password`.
2.  O backend processa a solicitação no endpoint público. O fluxo utiliza o `default_token_generator` do Django, que produz tokens temporários vinculados ao estado do usuário e não exige uma nova tabela no banco. O token expira em **900 segundos (15 minutos)**, configurado via `PASSWORD_RESET_TIMEOUT` nas settings.
3.  Para mitigar **enumeração de contas**, a API responde o mesmo status `200 OK` com payload idêntico para e-mails existentes ou inexistentes.

    > [!WARNING]
    > **Risco de Timing Attack (aberto):** O envio de e-mail é **síncrono** (SMTP direto). E-mails cadastrados recebem o e-mail e têm uma latência de resposta ligeiramente superior à de e-mails inexistentes (que retornam imediatamente). Um atacante paciente pode explorar essa diferença estatística para confirmar a existência de uma conta. **Mitigação futura recomendada:** mover o envio de e-mail para uma fila assíncrona (ex: Celery + Redis) para que ambos os caminhos retornem no mesmo tempo.

4.  O link recebido por e-mail contém `uid` (ID do usuário codificado em base64) e `token` (gerado de forma segura, expiração de 15 minutos). O token é de **uso único** — após a confirmação bem-sucedida, o estado do usuário muda e o token se torna inválido.
5.  O usuário acessa `/forgot-password/reset?uid=...&token=...`, preenche a nova senha atendendo aos critérios de força (mínimo 8 caracteres, maiúscula, número) e submete.
6.  Após a submissão, a API valida o token e uid. Em caso de sucesso, redefine a senha do usuário.
7.  **Invalidação de Sessões Anteriores (SimpleJWT nativo):** A revogação é implementada com o mecanismo nativo do `djangorestframework-simplejwt` (`CHECK_REVOKE_TOKEN = True`, `REVOKE_TOKEN_CLAIM = "hash_password"`). Os JWTs emitidos carregam um claim `hash_password` derivado da senha atual. Ao trocar a senha, todos os tokens anteriores passam a ter um claim desatualizado e são **rejeitados imediatamente** pelo endpoint de refresh e por qualquer endpoint autenticado — sem necessidade de blacklist por token.

---

## 6. Políticas de Segurança e LGPD

*   **Criptografia de Senhas:** Senhas são salvas no banco de dados com hashes seguros Django baseados em PBKDF2/Argon2. Nunca são salvas ou exibidas em texto plano.
*   **Cookies Seguros:**
    *   `auth_token`: `MaxAge=30min`, `SameSite=Lax`, `Path=/`.
    *   `auth_refresh_token`: `MaxAge=7d`, `SameSite=Lax`, `Path=/`.
    *   Em produção, os cookies devem possuir a diretiva `Secure` habilitada (transmissão restrita a conexões HTTPS).
    *   ⚠️ Os cookies **não** utilizam `HttpOnly`. A leitura via JavaScript é necessária para o mecanismo de silent refresh. Risco de XSS está documentado como gap futuro (ver Seção 1, Fora de Escopo).
*   **Invalidação de JWT por Alteração de Senha:**
    *   Implementada com o mecanismo nativo do SimpleJWT (`CHECK_REVOKE_TOKEN = True`).
    *   O claim `hash_password` é verificado a cada requisição autenticada e no endpoint de refresh.
    *   Não há dependência de blacklist por token — a invalidação é imediata e baseada no estado do usuário.
*   **Prevenção de Ataques de Força Bruta:**
    *   Qualquer login com falha incrementa `failed_login_attempts`.
    *   Na 5ª falha seguida, a conta é bloqueada por 30 minutos registrando `locked_until`.
    *   Logins efetuados com sucesso limpam o contador de falhas.
*   **Prevenção de Enumeração de Contas:**
    *   O endpoint `/api/v1/auth/login/` retorna a mesma mensagem de erro genérica para e-mail ou senha inválidos.
    *   O endpoint `/api/v1/auth/password/reset/` retorna `200 OK` com payload idêntico para e-mails existentes e inexistentes.
    *   ⚠️ **Risco residual (aberto):** O SMTP síncrono introduz diferença de latência mensurável. Ver Seção 5C para detalhes e plano de mitigação.
*   **Prevenção de Vazamento de Dados (Logs):**
    *   Dados confidenciais como senhas originais ou tokens JWT nunca devem ser impressos nos logs do console, do Django ou de auditoria.

---

## 7. Requisitos de Acessibilidade (WCAG AA)

*   **Navegação por teclado:** Formulários de Login/Registro e Edição de Perfil utilizam focos bem definidos (`focus:ring-2 focus:ring-primary focus:ring-offset-2`).
*   **Leitores de tela:**
    *   Inputs contam com `id`, `label` semanticamente conectado por `htmlFor` e mensagens de erro descritas por `aria-describedby` e `role="alert"`.
    *   O botão de mostrar/ocultar senha possui tag `aria-label` dinâmica para leitores anunciarem corretamente o estado do campo.
*   **Contraste Visual:** Cores definidas pelo Design System (Sálvia & Obsidian) atendem à taxa mínima de contraste de 4.5:1 para textos corporais.

---

## 8. Plano de Testes e Validação

### Testes de Integração e Unitários (Backend)
1.  `test_user_role_properties`: Valida se os papéis cadastrados refletem corretamente nas flags booleanas (`is_therapist`, `is_secretary`, `is_admin_role`).
2.  `test_failed_login_attempts_and_lockout`: Testa o fluxo de incremento de falhas de login e bloqueio temporário após 5 erros.
3.  `test_permission_classes`: Garante que as permissões DRF barram usuários sem permissão e liberam os autorizados.
4.  `test_owner_or_admin_permission`: Garante isolamento de objetos a nível de registro baseado no proprietário (`therapist`).
5.  `test_request_reset_valid_email`: Valida que o link contendo UID e token é enviado para e-mails cadastrados.
6.  `test_request_reset_nonexistent_email`: Valida que o endpoint retorna resposta idêntica e sem enviar e-mail.
7.  `test_confirm_reset_success`: Valida redefinição bem-sucedida alterando a senha no banco de dados.
8.  `test_confirm_reset_invalid_token`: Valida que tokens corrompidos são rejeitados com erro.
9.  `test_confirm_reset_mismatched_passwords`: Valida que senhas divergentes são rejeitadas.
10. `test_token_invalidation_after_password_reset`: Valida que tanto access tokens antigos quanto refresh tokens antigos são invalidados imediatamente (retornando 401 Unauthorized) após a senha ser redefinida.

### Testes Manuais de Fluxo (Frontend)
1.  **Validação de login correto:** Insere credenciais válidas e verifica redirecionamento e criação de cookies.
2.  **Validação de login incorreto:** Insere senha errada repetidamente e confere mensagem de bloqueio de conta.
3.  **Validação do Middleware (RBAC):** Efetua login com conta de `secretary` e tenta navegar digitando `/dashboard/records` na URL. O sistema deve barrar o acesso e redirecionar para a home do painel.

---

## 9. Critérios de Aceite para Conclusão

- [x] Todos os testes unitários e de integração de autenticação e permissões no backend passam com 100% de sucesso.
- [x] O frontend redireciona corretamente usuários não autenticados que tentam acessar rotas do `/dashboard`.
- [x] O fluxo de logout invalida o refresh token no banco de dados e limpa os cookies do navegador.
- [x] O silent refresh renova o token expirado sem interromper a experiência do usuário durante o uso do dashboard.
- [x] A redefinição de senha e fluxo de forgot password implementados: `/forgot-password` e `/forgot-password/reset` no frontend, com API backend em `/api/v1/auth/password/reset/` e `/api/v1/auth/password/reset/confirm/`.
- [x] Tokens JWT anteriores são invalidados imediatamente após alteração de senha (SimpleJWT nativo, `CHECK_REVOKE_TOKEN = True`).
- [ ] Acessibilidade WCAG AA validada em formulários utilizando leitores de tela básicos (validação manual pendente).
- [ ] **Gap de segurança (aberto):** Timing attack via SMTP síncrono no endpoint de reset. Mitigação: mover envio de e-mail para fila assíncrona (Celery). Risco aceito para este PR.
- [ ] **Gap de segurança (aberto):** Cookies JWT sem `HttpOnly`. Vulnerável a XSS. Dependente de refatoração da estratégia de sessão (BFF ou Next.js server-side cookies).
