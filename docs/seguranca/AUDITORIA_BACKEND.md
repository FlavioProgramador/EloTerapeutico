# Auditoria de Backend, Segurança e Proteção de Dados

## Identificação

- Projeto: Elo Terapêutico
- Branch de implementação: `security/auditoria-backend-dados`
- Commit-base analisado: `be07bb1e6e218ad715d436d0c62d1ed0e9fc1daf`
- Escopo: backend Django/DRF, billing Asaas, prontuário, documentos clínicos, logs, configurações de produção e Docker local.
- Regra operacional: nenhuma alteração desta auditoria foi aplicada diretamente na `main` ou em produção.

## Resumo executivo

O projeto já possuía controles relevantes: autenticação JWT com rotação e blacklist, invalidação após alteração de senha, Argon2, rate limiting, CORS restrito em produção, HSTS, HTTPS obrigatório, validação de assinatura real de anexos clínicos, escopo de documentos por proprietário e proteção de evoluções confidenciais.

A auditoria encontrou falhas concretas principalmente em minimização de dados financeiros, idempotência de webhook, logout, logs e persistência de arquivos em produção. As correções foram implementadas de forma incremental e acompanhadas por testes de regressão.

O projeto ainda não deve ser considerado multi-tenant seguro enquanto não existir um modelo explícito de organização/clínica e um vínculo obrigatório entre usuários, pacientes e recursos da organização.

## Achados corrigidos

| ID | Gravidade | Achado | Correção aplicada |
|---|---|---|---|
| SEC-001 | Alta | Checkout retornava o payload bruto do Asaas ao navegador. | Resposta substituída por allowlist com ID, status e URLs estritamente necessárias. |
| SEC-002 | Alta | Payloads financeiros brutos podiam duplicar CPF, tokens e dados PIX em JSON persistido. | Sanitização recursiva antes de salvar `WebhookEvent.payload`, `Payment.raw_payload` e metadata de assinatura. |
| SEC-003 | Alta | Replay com o mesmo `event_id` e payload alterado podia violar unicidade e gerar erro. | `event_id` passou a ser a chave principal de idempotência, com hash como fallback. |
| SEC-004 | Média | Usuário autenticado podia enviar ao logout o refresh token de outra conta. | Logout agora valida o claim de usuário antes de incluir o token na blacklist. |
| SEC-005 | Média | Comparação do segredo do webhook não era feita em tempo constante. | Validação alterada para `secrets.compare_digest`. |
| SEC-006 | Média | Downloads clínicos não definiam todos os cabeçalhos ant-cache e anti-sniffing. | Adicionados `no-store`, `Pragma`, `Expires`, `nosniff` e `Cross-Origin-Resource-Policy`. |
| SEC-007 | Média | Auditoria podia usar `str(obj)` e persistir nomes, e-mails ou conteúdo sensível. | Fallback substituído por rótulo técnico do modelo e chave primária; textos e cabeçalhos são normalizados e limitados. |
| SEC-008 | Média | `X-Forwarded-For` era aceito sem configuração explícita de confiança. | Cabeçalhos de proxy só são utilizados quando `TRUST_PROXY_CLIENT_IP_HEADERS=True`; IPs são validados. |
| SEC-009 | Média | Erros internos registravam a representação textual da exceção. | Logs internos registram somente tipo, view e request ID; respostas recebem correlação e `no-store`. |
| SEC-010 | Alta | Produção utilizava filesystem local para mídia clínica mesmo com configuração Azure disponível. | Adicionado suporte ao `AzureStorage`, URLs temporárias e opção de exigir storage privado na inicialização. |
| SEC-011 | Baixa | PostgreSQL do Docker local era publicado em todas as interfaces. | Porta restringida a `127.0.0.1`. |

## Testes adicionados

Foram adicionados testes para:

- ausência de payload bruto do gateway na API;
- rejeição de webhook com token inválido;
- redaction de CPF, tokens e dados PIX;
- replay com `event_id` estável;
- logout com token da própria conta e de conta diferente;
- cabeçalhos de download clínico;
- minimização de dados na auditoria;
- rejeição de IP encaminhado não confiável;
- request ID e proteção de respostas de erro;
- ausência de mensagem sensível em logs de exceção.

Também foi criado o workflow `.github/workflows/backend-security.yml`, com:

- `python manage.py check`;
- verificação de migrations pendentes;
- Ruff;
- pytest;
- Bandit;
- pip-audit.

Bandit e pip-audit foram configurados como diagnósticos não bloqueantes inicialmente, para que vulnerabilidades preexistentes possam ser inventariadas antes de torná-los gates obrigatórios.

## Riscos residuais prioritários

### R-001 — Ausência de tenant/organização explícita

**Gravidade: crítica se o sistema atender múltiplas clínicas.**

O modelo atual de usuário define papéis globais, mas não possui vínculo obrigatório com organização ou clínica. O controle de acesso a pacientes permite acesso amplo para administradores e secretárias. Alterar essa regra isoladamente poderia quebrar o funcionamento atual, portanto não foi feita uma mudança automática.

Antes de comercializar o sistema como SaaS multi-clínica, implementar:

1. `Organization` ou `Clinic`;
2. associação obrigatória de usuários e recursos ao tenant;
3. papéis por organização, não globais;
4. selectors/managers com escopo obrigatório;
5. constraints no banco;
6. testes cruzados entre organizações para listagem, detalhe, alteração, exclusão, relatórios, cache, workers e arquivos.

### R-002 — Tokens acessíveis ao JavaScript

**Gravidade: alta.**

O frontend grava access e refresh tokens por JavaScript usando `cookies-next`. Esses cookies não podem ser `HttpOnly`, portanto um XSS bem-sucedido pode acessá-los.

A correção completa requer uma mudança coordenada:

1. backend emitir cookies `HttpOnly`, `Secure` e `SameSite`;
2. frontend deixar de ler tokens;
3. cliente enviar `withCredentials`;
4. implementar proteção CSRF adequada para autenticação por cookie;
5. adaptar refresh, logout e middleware Next;
6. revisar CORS com credenciais;
7. criar testes de sessão e CSRF.

Não basta marcar `secure` no cliente; isso protege o transporte, mas não protege contra XSS.

### R-003 — Timing da recuperação de senha

**Gravidade: média.**

A resposta pública é genérica e existe rate limit, porém o e-mail ainda é enviado de forma síncrona somente para contas existentes. A latência SMTP pode permitir diferenciação estatística.

Solução recomendada: fila persistida de e-mails com worker separado, de forma que a requisição apenas crie um job uniforme e retorne imediatamente. Não utilizar thread iniciada dentro da requisição.

### R-004 — Storage privado depende de configuração

**Gravidade: alta em produção.**

O backend utiliza Azure Blob privado quando `AZURE_STORAGE_CONNECTION_STRING` está presente. Para impedir fallback acidental para filesystem local em produção, definir:

```env
PRIVATE_MEDIA_STORAGE_REQUIRED=True
AZURE_STORAGE_CONNECTION_STRING=<segredo no ambiente>
AZURE_CONTAINER_NAME=elo-terapeutico
AZURE_URL_EXPIRATION_SECS=300
```

O container Azure deve existir previamente e não possuir acesso público.

### R-005 — Validação automatizada pendente de execução

O ambiente utilizado nesta auditoria não conseguiu clonar o repositório ou executar Docker/pytest localmente. O workflow de segurança foi adicionado para executar a validação no GitHub Actions. Nenhuma alegação de testes aprovados deve ser feita até existir uma execução concluída com sucesso.

## Checklist antes de merge

- [ ] Executar o workflow `Backend Security`.
- [ ] Corrigir falhas de Ruff ou pytest.
- [ ] Revisar resultados de Bandit e pip-audit.
- [ ] Executar `python manage.py check --deploy` com settings e segredos equivalentes à produção.
- [ ] Validar acesso ao container Azure privado.
- [ ] Confirmar que arquivos existentes foram migrados do filesystem para Azure antes de exigir storage privado.
- [ ] Testar checkout e webhook no sandbox do Asaas.
- [ ] Confirmar que nenhum consumidor depende de `raw_gateway_response`.
- [ ] Testar logout e renovação de token no frontend.
- [ ] Revisar o diff e fazer merge somente após aprovação.

## Classificação atual

**Recomendado apenas para homologação até que o workflow passe e o storage privado seja validado.**

Para operação multi-clínica, o projeto permanece **não recomendado para produção** até a implementação do isolamento por organização.
