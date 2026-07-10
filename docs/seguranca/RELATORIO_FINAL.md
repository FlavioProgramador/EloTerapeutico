# Relatório Final — Auditoria de Backend e Proteção de Dados

## Resultado

A auditoria técnica foi implementada na branch `security/auditoria-backend-dados`, sem alteração direta da `main`, sem merge automático e sem publicação em produção.

O último commit de código integralmente validado foi:

```text
546b4b5547566fb608f201bcf643b6a88170581b
```

## Situação antes das correções

Foram confirmados riscos nas seguintes áreas:

- exposição excessiva de respostas e payloads financeiros;
- idempotência e autenticação de webhook;
- logout de tokens pertencentes a outra conta;
- enumeração de conta por estado de login;
- acesso administrativo implícito a conteúdo clínico confidencial;
- rotas antigas contornando views seguras;
- exportações clínicas acessíveis entre profissionais com acesso ao mesmo paciente;
- metadados confidenciais visíveis no resumo do prontuário;
- uploads validados somente por extensão e MIME declarado;
- logs com possibilidade de PII, conteúdo clínico ou detalhe de exceção;
- segredos de produção fracos, reutilizados ou com placeholders;
- dependência WeasyPrint vulnerável à `CVE-2026-49452`;
- storage clínico local como fallback de produção;
- hosts e portas locais excessivamente permissivos.

## Controles implementados

### Autenticação

- respostas indistinguíveis para e-mail inexistente, senha incorreta, conta bloqueada e conta inativa;
- validação oficial de força de senha no cadastro, troca e redefinição;
- refresh token validado contra o usuário autenticado antes do logout;
- comparação em tempo constante para hashes e segredos aplicáveis;
- logs de reset de senha sem endereço, token ou traceback.

### Prontuário e dados clínicos

- rotas públicas apontando para views seguras;
- evolução confidencial acessível somente ao autor ou por permissão clínica explícita;
- mesma regra aplicada ao Django Admin;
- documentos confidenciais protegidos em lista, detalhe, atualização e download;
- workspace sem contagem, data, ID ou anexo de evolução confidencial não autorizada;
- exportações isoladas por criador;
- download e retry de exportação alheia exigindo papel administrativo e permissão explícita;
- worker respeitando a autorização clínica no momento de gerar o PDF;
- downloads com cabeçalhos ant-cache, anti-sniffing e same-origin.

### Uploads

- assinatura real para PDF, JPEG e PNG;
- texto limitado a UTF-8 e sem conteúdo binário;
- DOCX validado como pacote OpenXML legítimo;
- proteção contra ZIP bomb, path traversal e arquivos internos criptografados;
- nome original sanitizado e armazenamento físico com identificador não previsível.

### Billing e Asaas

- preço do plano definido pelo backend;
- payload bruto removido das respostas do checkout;
- respostas do gateway reduzidas a allowlist;
- erros internos não devolvidos ao navegador;
- webhook autenticado com comparação em tempo constante;
- idempotência por `event_id` e hash de fallback;
- dados sensíveis removidos antes da persistência de payloads e metadados;
- logs financeiros sem traceback ou conteúdo do payload.

### Configuração e infraestrutura

- placeholders, segredos curtos e reutilização de chaves rejeitados em produção;
- Django, JWT, criptografia e webhook exigem segredos distintos;
- suporte a Azure Blob privado com URL temporária;
- opção fail-closed para impedir filesystem local em produção;
- headers de proxy confiáveis somente com opt-in;
- PostgreSQL local restrito ao loopback;
- `ALLOWED_HOSTS` de desenvolvimento sem `0.0.0.0` por padrão;
- WeasyPrint atualizado para a linha 69.x.

### Observabilidade e auditoria

- audit log registra rótulo técnico e ID, sem `str(obj)` como fallback;
- IP encaminhado validado e somente aceito quando o proxy é explicitamente confiável;
- erros recebem identificador de correlação;
- logs de falha registram tipo técnico, não conteúdo da exceção;
- respostas de erro e downloads sensíveis usam `no-store`.

## Validação automatizada

| Validação | Resultado |
|---|---|
| Django system check | Aprovado |
| Migrations pendentes | Nenhuma |
| Pre-commit/Ruff | Aprovado |
| Pytest | 242 aprovados |
| Warnings | 11 |
| Cobertura total no pytest | 63,17% |
| Coverage XML — linhas | 68,11% |
| Bandit | Aprovado como gate obrigatório |
| pip-audit | Aprovado como gate obrigatório |
| CodeQL | Aprovado |
| Dependency Security | Aprovado |
| Docker Images | Aprovado |
| Frontend CI | Aprovado |

O workflow de segurança publica relatórios de Ruff, Bandit e pip-audit como artefatos. Os três resultados são avaliados pelo gate final e qualquer falha bloqueia a validação.

## Riscos residuais

### Crítico para operação multi-clínica

Não existe ainda um tenant explícito. Os papéis `admin` e `secretary` são globais e não estão vinculados a uma organização. O sistema não deve ser comercializado como multi-clínica antes da implementação de `Organization`/`Clinic`, memberships, constraints e testes cruzados.

### Alto

- tokens ainda são acessíveis ao JavaScript no frontend;
- storage privado depende de configuração operacional e migração dos arquivos existentes;
- restauração de backup ainda precisa ser testada;
- rotação da chave de criptografia precisa de procedimento operacional validado.

### Médio

- envio de e-mail de recuperação permanece síncrono e pode produzir diferença estatística de latência;
- checkout e webhook precisam de teste completo no sandbox Asaas;
- Azure Blob precisa ser validado com container privado e expiração real das URLs;
- `check --deploy` deve ser executado com settings equivalentes ao ambiente final.

## Classificação

- **Homologação:** recomendada.
- **Produção individual:** condicionada à validação operacional de Azure, Asaas, backup e settings de produção.
- **Produção multi-clínica:** não recomendada.

## Estado do PR

O PR `#134` permanece em modo rascunho. Não foi realizado merge, publicação ou alteração direta da `main`.
