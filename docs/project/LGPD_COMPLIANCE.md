# Diretrizes de Conformidade LGPD - Elo Terapêutico

Este documento detalha as medidas técnicas e administrativas adotadas no **Elo Terapêutico** para garantir a total conformidade com a **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)**.

Dado que o sistema armazena prontuários, evoluções clínicas e anamneses, lidamos diretamente com **dados pessoais sensíveis** (Art. 5º, II da LGPD). Portanto, a privacidade e a segurança das informações são tratadas como requisitos de arquitetura prioritários desde o primeiro dia de desenvolvimento.

---

## 🔒 1. Segurança e Proteção dos Dados Sensíveis

### 1.1 Criptografia em Repouso (Encryption at Rest)
* **Objetivo:** Garantir que, mesmo em caso de vazamento ou acesso não autorizado ao banco de dados PostgreSQL, as informações clínicas dos pacientes permaneçam ilegíveis.
* **Implementação:**
  * O campo contendo a evolução clínica (`Evolution.content`) e histórico de anamneses é criptografado a nível de aplicação antes de ser gravado no banco de dados.
  * Utiliza-se a biblioteca `django-cryptography` (que encapsula criptografia simétrica AES-256).
  * A chave de criptografia (`FIELD_ENCRYPTION_KEY`) é armazenada como variável de ambiente no servidor (Azure App Service) e nunca é commitada no repositório Git.

### 1.2 Criptografia em Trânsito (Encryption in Transit)
* **Objetivo:** Impedir interceptação de dados na rede (ataques Man-in-the-Middle).
* **Implementação:**
  * Comunicação via **HTTPS** forçada em produção (HTTP Strict Transport Security - HSTS).
  * Tokens de autenticação JWT transferidos e armazenados de maneira segura no frontend através de cookies com as diretivas `HttpOnly`, `Secure` e `SameSite=Strict`, protegendo o sistema contra ataques XSS e CSRF.

---

## 👥 2. Controle de Acessos e Privilégios (RBAC)

O sistema opera sob a política de **menor privilégio necessário** (Least Privilege):
* **Terapeuta:** Acesso total aos dados pessoais e clínicos (prontuário/evolução) dos seus pacientes vinculados.
* **Secretária / Recepção:** Acesso estritamente restrito à agenda (datas e horários) e dados básicos de contato para agendamentos. **Sem acesso** a prontuários, diagnósticos ou anotações terapêuticas.
* **Paciente (se aplicável futuramente):** Acesso apenas às suas próprias informações pessoais e solicitações de agendamento.

---

## 📝 3. Trilha de Auditoria (Audit Trail)

Toda leitura ou modificação de dados sensíveis de pacientes deve ser rastreável.
* **Registro de Logs de Acesso:**
  * Sempre que o endpoint de evolução clínica (`/api/records/evolution/`) for acessado por meio de um método `GET`, `POST` ou `PATCH`, o sistema gera um registro de log imutável no banco de dados.
  * O log contém: `UserID` (do terapeuta), `PatientID` (do paciente visualizado), `Timestamp` (data e hora exata) e `Action` (Visualizou, Criou, Alterou).
  * Estes logs de auditoria não podem ser alterados ou deletados pelos usuários da aplicação.

---

## 🔄 4. Direitos do Titular (Paciente)

De acordo com o Art. 18 da LGPD, os pacientes possuem direitos específicos sobre seus dados que são assegurados pelo sistema:

### 4.1 Direito de Acesso e Portabilidade
* O sistema fornece ao terapeuta um mecanismo de exportação completa do prontuário do paciente (em formato PDF assinado digitalmente ou JSON estruturado) para entrega direta ao titular, caso solicitado.

### 4.2 Direito ao Esquecimento e Anonimização
* Quando um paciente solicitar a exclusão de seus dados, o sistema realiza um processo de **anonimização mitigada** em vez de uma exclusão destrutiva direta (para preservar dados fiscais e relatórios gerenciais):
  * **Dados Clínicos (Evoluções e Anamneses):** São permanentemente deletados do banco de dados (exclusão física).
  * **Dados Fiscais / Transações Financeiras:** São mantidos para fins de conformidade com a legislação tributária brasileira. No entanto, o vínculo com o paciente é desfeito (o paciente vira um registro anonimizado como "Paciente Anonimizado #12345"), removendo CPF, Nome, E-mail e Telefone.

---

## ⏳ 5. Retenção de Dados e Regras de Conselhos (CRP/CFM)

A LGPD permite a guarda de dados para cumprimento de obrigação legal ou regulatória pelo controlador (Art. 16, I).
* **Guarda Obrigatória:** Os conselhos federais de psicologia (CRP) e medicina (CFM) exigem que os prontuários sejam mantidos por um período mínimo de **5 anos** (CRP) a **20 anos** (CFM) a partir do último registro. Portanto, solicitações de exclusão de prontuários ativos dentro do prazo legal podem ser legalmente recusadas pelo terapeuta, mantendo apenas a inativação do cadastro.
* **Integridade dos Registros ( CRP ):** Para garantir que as evoluções clínicas não sejam editadas retroativamente para alterar o histórico do paciente, o backend impede qualquer alteração em uma evolução clínica após **48 horas** de sua publicação. Modificações posteriores só podem ser feitas via **Termo Aditivo** (Retificação), mantendo o registro original intacto.
