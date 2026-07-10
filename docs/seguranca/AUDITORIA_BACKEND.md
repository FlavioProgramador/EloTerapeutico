# Auditoria de Backend, Segurança e Proteção de Dados

## Identificação

- Projeto: Elo Terapêutico
- Branch de implementação: `security/auditoria-backend-dados`
- Pull request de validação: `#134` — mantido em modo rascunho
- Commit-base analisado: `be07bb1e6e218ad715d436d0c62d1ed0e9fc1daf`
- Último commit de código validado: `546b4b5547566fb608f201bcf643b6a88170581b`
- Escopo: backend Django/DRF, autenticação, billing Asaas, prontuário, documentos clínicos, exportações, logs, configurações de produção, dependências e Docker.
- Regra operacional: nenhuma alteração desta auditoria foi aplicada diretamente na `main`, mesclada ou publicada em produção.

## Resumo executivo

O projeto já possuía controles relevantes, incluindo JWT com rotação e blacklist, invalidação de tokens após alteração de senha, Argon2, rate limiting, CORS restrito em produção, HSTS, HTTPS obrigatório e regras iniciais de confidencialidade clínica.

A auditoria encontrou e corrigiu falhas concretas em:

- minimização e persistência de dados financeiros;
- idempotência e autenticação do webhook Asaas;
- autorização do logout;
- enumeração de contas no login;
- validação de senhas;
- autorização de documentos e exportações clínicas;
- exposição de metadados confidenciais no workspace;
- acesso administrativo a evoluções confidenciais;
- validação estrutural de uploads;
- logs e respostas de erro;
- validação de segredos de produção;
- configuração de hosts de desenvolvimento;
- dependência vulnerável do gerador de PDF.

As correções foram aplicadas de forma incremental, com testes de regressão, análise estática e validação completa no GitHub Actions.

O projeto **ainda não deve ser considerado multi-tenant seguro** enquanto não existir um modelo explícito de organização/clínica e vínculo obrigatório entre usuários, pacientes e recursos de cada tenant.

## Achados corrigidos

| ID | Gravidade | Achado | Correção aplicada |
|---|---|---|---|
| SEC-001 | Alta | Checkout retornava o payload bruto do Asaas ao navegador. | Resposta substituída por allowlist com ID, status e URLs estritamente necessárias. |
| SEC-002 | Alta | Payloads financeiros podiam persistir CPF, tokens e dados PIX duplicados. | Sanitização recursiva antes de salvar payloads e metadados financeiros. |
| SEC-003 | Alta | Replay com o mesmo `event_id` e payload alterado podia violar idempotência. | `event_id` passou a ser a chave principal, com hash como fallback. |
| SEC-004 | Média | Usuário autenticado podia enviar ao logout o refresh token de outra conta. | O token agora precisa pertencer ao usuário autenticado antes de entrar na blacklist. |
| SEC-005 | Média | Comparação do segredo do webhook não era feita em tempo constante. | Validação alterada para `secrets.compare_digest`. |
| SEC-006 | Alta | Rotas públicas usavam classes antigas de documentos, ignorando proteções mais novas. | URLs passaram a apontar explicitamente para as views seguras. |
| SEC-007 | Alta | Superusuário podia acessar documentos confidenciais sem autorização clínica explícita. | Acesso limitado ao autor ou a usuário/grupo com permissão clínica explicitamente atribuída. |
| SEC-008 | Alta | Administrador podia listar, reprocessar ou baixar exportações criadas por outro profissional. | Exportações agora são isoladas por criador; acesso cruzado exige papel administrativo e permissão clínica explícita. |
| SEC-009 | Alta | Workspace podia revelar documentos, contagens e datas de evoluções confidenciais. | Documentos e métricas são calculados somente sobre evoluções visíveis ao usuário. |
| SEC-010 | Alta | Django Admin ignorava a regra de confidencialidade das evoluções. | Queryset do backoffice aplica a mesma autorização explícita usada pela API. |
| SEC-011 | Média | Downloads clínicos não definiam todos os cabeçalhos ant-cache e anti-sniffing. | Adicionados `no-store`, `Pragma`, `Expires`, `nosniff` e `Cross-Origin-Resource-Policy`. |
| SEC-012 | Alta | Uploads `.pdf`, `.txt` e `.docx` confiavam excessivamente em extensão/MIME informado. | Validação de assinatura real, UTF-8, estrutura DOCX, ZIP bomb, caminhos internos e arquivos criptografados. |
| SEC-013 | Média | Login revelava existência da conta por mensagens de bloqueio/inatividade. | E-mail inexistente, senha incorreta, conta bloqueada e conta inativa retornam resposta pública indistinguível. |
| SEC-014 | Média | Cadastro, troca e redefinição de senha não aplicavam todos os validadores do Django. | Validadores oficiais são executados nos três fluxos. |
| SEC-015 | Alta | Produção podia iniciar com placeholders, segredos curtos ou mesma chave em finalidades distintas. | Inicialização rejeita valores fracos e reutilização entre Django, JWT, criptografia e webhook. |
| SEC-016 | Média | Erros internos do gateway podiam ser devolvidos ao cliente. | API retorna mensagem genérica; logs guardam apenas operação e contexto mínimo. |
| SEC-017 | Média | Logs podiam conter representação de objetos, tracebacks e mensagens de exceção sensíveis. | Logs guardam IDs, tipo técnico da exceção e metadados mínimos, sem payload clínico/financeiro. |
| SEC-018 | Alta | WeasyPrint 68.1 possuía `CVE-2026-49452`. | Dependência atualizada para `weasyprint>=69.0,<70.0` e validada pelo `pip-audit`. |
| SEC-019 | Média | `ALLOWED_HOSTS` de desenvolvimento incluía `0.0.0.0` por padrão. | Padrão limitado a `localhost` e `127.0.0.1`; hosts adicionais exigem configuração explícita. |
| SEC-020 | Média | Auditoria podia usar `str(obj)` e persistir PII ou conteúdo sensível. | Fallback substituído pelo rótulo técnico do modelo e chave primária. |
| SEC-021 | Média | `X-Forwarded-For` era aceito sem configuração explícita. | Cabeçalhos de proxy só são usados quando `TRUST_PROXY_CLIENT_IP_HEADERS=True`; IPs são validados. |
| SEC-022 | Alta | Produção utilizava filesystem local para mídia mesmo com Azure disponível. | Adicionado Azure Storage privado, URLs temporárias e opção fail-closed via `PRIVATE_MEDIA_STORAGE_REQUIRED`. |
| SEC-023 | Baixa | PostgreSQL do Docker local era publicado em todas as interfaces. | Porta restringida a `127.0.0.1`. |

## Validação executada

### Suíte funcional

- Resultado: **242 testes aprovados**;
- Warnings: **11**;
- Duração da execução validada: **20,67 segundos**;
- Cobertura total exibida pelo pytest: **63,17%**;
- Cobertura de linhas no `coverage.xml`: **68,11%**;
- Migrations pendentes: **nenhuma**.

### Gates automatizados

O workflow `.github/workflows/backend-security.yml` executa e bloqueia o PR quando houver falha em:

- `python manage.py check`;
- verificação de migrations;
- Ruff;
- pytest;
- Bandit;
- pip-audit.

Bandit e pip-audit são **gates obrigatórios**. Os relatórios são publicados como artefatos mesmo em caso de falha.

### Workflows aprovados

No commit validado, concluíram com sucesso:

- Django CI;
- Backend Security;
- CodeQL;
- Dependency Security;
- Docker Images;
- Frontend CI.

## Riscos residuais prioritários

### R-001 — Ausência de tenant/organização explícita

**Gravidade: crítica se o sistema atender múltiplas clínicas.**

O modelo atual de usuário define papéis globais, mas não possui vínculo obrigatório com organização ou clínica. O controle de acesso a pacientes permite escopo amplo para administradores e secretárias. Alterar essa regra isoladamente poderia quebrar dados e fluxos existentes, portanto não foi feita uma migração automática.

Antes de comercializar o sistema como SaaS multi-clínica, implementar:

1. `Organization` ou `Clinic`;
2. associação obrigatória de usuários e recursos ao tenant;
3. papéis por organização, não globais;
4. selectors/managers com escopo obrigatório;
5. constraints no banco;
6. testes cruzados para API, admin, relatórios, cache, workers e arquivos.

### R-002 — Tokens acessíveis ao JavaScript

**Gravidade: alta.**

O frontend grava access e refresh tokens por JavaScript. Uma correção completa requer migração coordenada para cookies `HttpOnly`, proteção CSRF, `withCredentials`, adaptação de refresh/logout e revisão do middleware Next.

### R-003 — Timing da recuperação de senha

**Gravidade: média.**

A resposta pública é genérica e existe rate limit, mas o e-mail ainda é enviado de forma síncrona somente quando a conta existe. A mitigação recomendada é uma fila persistida de e-mails com worker separado.

### R-004 — Storage privado depende de configuração e migração

**Gravidade: alta em produção.**

Definir em produção:

```env
PRIVATE_MEDIA_STORAGE_REQUIRED=True
AZURE_STORAGE_CONNECTION_STRING=<segredo no ambiente>
AZURE_CONTAINER_NAME=elo-terapeutico
AZURE_URL_EXPIRATION_SECS=300
```

O container deve ser privado. Arquivos já existentes precisam ser migrados e verificados antes de ativar o modo fail-closed.

### R-005 — Integrações externas precisam de validação operacional

**Gravidade: média.**

Ainda é necessário validar em ambiente de homologação:

- checkout e webhooks reais no sandbox Asaas;
- expiração e autorização de URLs Azure;
- restauração de backup;
- rotação da chave de criptografia de campos;
- observabilidade no Azure Monitor.

## Checklist antes de merge

- [x] Executar Django check e verificação de migrations.
- [x] Executar a suíte completa de testes.
- [x] Executar Ruff.
- [x] Executar Bandit como gate obrigatório.
- [x] Executar pip-audit como gate obrigatório.
- [x] Executar CodeQL.
- [x] Validar build das imagens Docker.
- [x] Validar frontend CI.
- [ ] Executar `python manage.py check --deploy` com segredos e settings equivalentes à produção.
- [ ] Validar Azure Blob privado e migração dos arquivos existentes.
- [ ] Testar checkout, cancelamento, mudança de plano e webhooks no sandbox Asaas.
- [ ] Testar recuperação de backup.
- [ ] Confirmar que nenhum consumidor externo depende do antigo `raw_gateway_response`.
- [ ] Testar logout, refresh e expiração no navegador.
- [ ] Revisar o diff e aprovar manualmente o PR.

## Classificação atual

- **Homologação:** recomendada, com os workflows aprovados.
- **Produção para profissional individual:** possível somente após concluir os requisitos operacionais de storage, Asaas, backup e `check --deploy`.
- **Produção multi-clínica/multi-tenant:** **não recomendada** até implementar isolamento por organização.

O PR permanece em modo rascunho e não deve ser mesclado automaticamente.
