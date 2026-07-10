# Modelo de Ameaças — Elo Terapêutico

## Escopo

Este documento descreve ameaças relevantes ao backend, às integrações financeiras, ao prontuário clínico, aos arquivos e à infraestrutura do Elo Terapêutico.

Metodologia utilizada: **STRIDE**, complementada por análise de privacidade e abuso de regras de negócio.

## Ativos críticos

- credenciais, access tokens e refresh tokens;
- dados pessoais e dados pessoais sensíveis dos pacientes;
- prontuários, evoluções, anamneses e planos terapêuticos;
- documentos clínicos e arquivos exportados;
- dados financeiros e informações de cobrança;
- segredos do Asaas, banco, SMTP, JWT e criptografia de campos;
- registros de auditoria;
- backups;
- configurações de produção;
- vínculos entre terapeutas, pacientes e profissionais compartilhados.

## Atores

- terapeuta legítimo;
- secretária legítima;
- administrador legítimo;
- profissional com acesso compartilhado;
- usuário autenticado mal-intencionado;
- usuário de outra clínica ou organização;
- atacante externo sem autenticação;
- conta comprometida;
- integração externa comprometida;
- operador de infraestrutura com acesso privilegiado.

## Fronteiras de confiança

1. Navegador ↔ frontend Next.js.
2. Frontend ↔ API Django/DRF.
3. API ↔ PostgreSQL.
4. API ↔ Redis/cache.
5. API ↔ Azure Blob Storage.
6. API ↔ Asaas.
7. API ↔ SMTP.
8. API ↔ workers e filas persistidas.
9. Administrador Django ↔ dados internos.
10. GitHub Actions ↔ código e dependências.

## Matriz STRIDE

### Spoofing — falsificação de identidade

| Ameaça | Cenário | Controle atual | Ação necessária |
|---|---|---|---|
| Roubo de JWT | XSS lê cookies criados pelo JavaScript. | Tokens expiram, refresh rotaciona e pode ser revogado. | Migrar para cookies HttpOnly emitidos pelo backend e proteção CSRF. |
| Falsificação de webhook | Requisição externa simula evento do Asaas. | Token obrigatório em produção e comparação em tempo constante. | Rotacionar segredo, limitar origem quando viável e monitorar falhas. |
| IP forjado em auditoria | Cliente envia `X-Forwarded-For` arbitrário. | Cabeçalhos só são aceitos quando a confiança no proxy está habilitada. | Manter proxy gerenciado e impedir acesso direto ao backend. |

### Tampering — adulteração

| Ameaça | Cenário | Controle atual | Ação necessária |
|---|---|---|---|
| Alteração de valor no checkout | Cliente envia preço inferior. | Serializer substitui o valor pelo preço do plano no backend. | Manter teste de regressão e não aceitar descontos sem regra de domínio. |
| Replay de webhook | Mesmo evento é reenviado ou alterado. | Idempotência por `event_id`, hash como fallback e transação atômica. | Monitorar eventos conflitantes e reconciliar periodicamente com o gateway. |
| Alteração de prontuário consolidado | Usuário tenta sobrescrever evolução após prazo. | Regra de bloqueio e aditivos existentes. | Manter testes de 48 horas e trilha de retificação. |
| Alteração de auditoria | Usuário tenta editar ou apagar registro. | Modelo impede `save` posterior e `delete` comum. | Restringir também operações diretas no banco e definir retenção. |

### Repudiation — repúdio

| Ameaça | Cenário | Controle atual | Ação necessária |
|---|---|---|---|
| Negação de acesso a prontuário | Usuário afirma não ter consultado registro. | AuditLog registra ator, ação, objeto, IP e user-agent. | Adicionar escopo organizacional quando tenancy existir. |
| Negação de exportação | Arquivo clínico é baixado sem rastreabilidade. | Downloads e exportações relevantes são auditados. | Garantir que todos os endpoints de arquivo utilizem o mesmo serviço de auditoria. |
| Negação de evento financeiro | Estado local muda por webhook. | WebhookEvent persiste ID, tipo, hash e resultado. | Definir política de retenção e reconciliação. |

### Information Disclosure — divulgação de informação

| Ameaça | Cenário | Controle atual | Ação necessária |
|---|---|---|---|
| Payload bruto do Asaas no navegador | Resposta inclui dados adicionados pelo gateway. | Resposta pública usa allowlist explícita. | Manter teste contra novos campos sensíveis. |
| Dados financeiros duplicados em JSON | CPF, token e PIX ficam em raw payload. | Redaction recursiva antes da persistência. | Criptografar campos funcionais que precisem permanecer armazenados. |
| Documento clínico em cache | Browser/proxy mantém cópia após download. | `no-store`, `nosniff` e política de mesma origem. | Validar headers também no proxy e CDN. |
| Conteúdo sensível em logs | `str(obj)` ou exceção inclui dados pessoais. | Representação técnica e logging sem mensagem bruta da exceção. | Implementar redaction central no pipeline de observabilidade. |
| Arquivo clínico em storage público | URL permanente permite download sem autorização. | Suporte a Azure privado e URLs temporárias. | Exigir storage privado em produção e verificar acesso público do container. |

### Denial of Service — indisponibilidade

| Ameaça | Cenário | Controle atual | Ação necessária |
|---|---|---|---|
| Tentativas de login/reset em massa | Atacante consome CPU/SMTP. | Rate limits por IP e bloqueio de conta. | Usar cache compartilhado Redis e fila de e-mail. |
| Upload excessivo | Arquivos grandes consomem memória e storage. | Limite de tamanho, extensão, MIME e assinatura real. | Adicionar quota por usuário/organização e scanner antimalware. |
| Relatórios/exportações pesadas | Geração síncrona bloqueia workers web. | Exportação clínica possui worker persistido. | Aplicar padrão equivalente aos demais relatórios pesados. |
| Webhooks concorrentes | Replays disputam constraints. | Transação, IDs únicos e idempotência. | Avaliar lock por evento em carga elevada. |

### Elevation of Privilege — elevação de privilégio

| Ameaça | Cenário | Controle atual | Ação necessária |
|---|---|---|---|
| Papel administrativo global | Admin/secretária acessa pacientes fora da clínica. | Não existe isolamento organizacional completo. | Implementar Organization/Clinic e papéis por tenant antes de produção multi-clínica. |
| IDOR em paciente/documento | Usuário altera ID na URL. | Querysets e mixins aplicam vínculo ao paciente/proprietário. | Manter testes cruzados para cada novo endpoint. |
| Logout de outra conta | Usuário envia refresh token alheio. | Token agora é vinculado ao usuário autenticado. | Manter testes e registrar abuso recorrente. |
| Campo protegido no payload | Cliente define owner, author, role ou status. | Vários serializers definem valores no servidor. | Continuar auditoria serializer por serializer e usar read-only fields. |

## Cenários prioritários

### 1. Vazamento entre clínicas

Risco mais relevante para a evolução do produto. O modelo atual suporta profissionais e papéis, mas não possui uma entidade organizacional obrigatória. Enquanto isso não for implementado, administradores e secretárias devem ser considerados globais.

### 2. Comprometimento do navegador

Como os tokens são acessíveis ao JavaScript, qualquer XSS pode comprometer a sessão. Sanitização de conteúdo clínico reduz a superfície, mas não substitui cookies HttpOnly.

### 3. Comprometimento do gateway ou webhook

Mesmo com token correto, payloads precisam ser tratados como entrada não confiável. Valores e referências devem ser conferidos contra entidades locais, e eventos devem ser idempotentes.

### 4. Exposição de arquivos

Arquivos clínicos devem existir somente em armazenamento privado. Downloads precisam passar pela autorização da aplicação ou utilizar URLs assinadas curtas emitidas após autorização.

## Controles de aceitação antes de produção

- isolamento por organização implementado e testado;
- storage privado obrigatório e container sem acesso público;
- workflow de segurança aprovado;
- teste de restauração de backup executado;
- rotação documentada de segredos e chave de criptografia;
- proteção de sessão por cookie HttpOnly ou mitigação equivalente aprovada;
- workers e cache compartilhado configurados;
- monitoramento de falhas de login, webhook e exportação;
- plano de resposta a incidentes e comunicação de violação de dados.
