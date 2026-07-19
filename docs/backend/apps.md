# Apps e responsabilidades

Este inventário reflete os apps registrados em `config.settings.base.LOCAL_APPS` e a organização atual do backend.

## Resumo

| App | Responsabilidade principal | Dados sensíveis ou críticos |
| --- | --- | --- |
| `core` | Infraestrutura compartilhada, API, campos, validações, exceções e qualidade arquitetural | Configuração, criptografia e tratamento de erros |
| `users` | Usuários, perfil, autenticação, credenciais e recuperação de acesso | Credenciais, sessões e dados pessoais |
| `patients` | Cadastro, responsáveis, importação, exportação e ciclo de vida de pacientes | Dados pessoais e contatos |
| `records` | Prontuário, anamnese, evoluções, aditivos, anexos e exportações | Dados clínicos e autoria |
| `agenda` | Consultas, recorrências, salas, pacotes, lembretes e telemedicina | Agenda, pacientes e vínculos financeiros |
| `financeiro` | Receitas, despesas, pagamentos, mensalidades, reversões e exportações | Valores, vencimentos e situação financeira |
| `documents` | Templates, sequências, documentos gerados, PDF e integridade | Documentos clínicos e assinaturas |
| `reports` | Indicadores e exportações de agenda, pacientes e financeiro | Dados agregados e exportáveis |
| `forms` | Templates, campos, submissões e respostas | Respostas possivelmente clínicas |
| `billing` | Planos, assinaturas, cobranças, checkout e webhooks | Pagamentos, assinatura e dados do gateway |
| `communications` | Notificações, templates, automações, fila e links públicos | Destinos de contato e tokens públicos |
| `audit` | Registro imutável de ações sensíveis | Metadados de acesso e alterações |

## `apps.core`

Responsabilidades:

- paginação e contratos comuns da API;
- exceções e tratamento padronizado de erros;
- campos criptografados e validações compartilhadas;
- integrações e utilitários transversais;
- dashboard e recursos internos do Django Admin;
- verificações automáticas da arquitetura.

Cuidados:

- não transformar `core` em depósito genérico de regras de domínio;
- classes compartilhadas não devem depender de apps específicos sem necessidade;
- mensagens de erro públicas não devem revelar detalhes internos.

## `apps.users`

Responsabilidades:

- model de usuário customizado;
- login, refresh e logout JWT;
- bloqueio após tentativas falhas;
- alteração e recuperação de senha;
- perfil e configurações do terapeuta;
- health check da aplicação.

Services de credenciais devem invalidar sessões ou tokens quando a regra exigir e evitar mensagens que permitam enumeração de contas.

## `apps.patients`

Responsabilidades:

- cadastro e atualização de pacientes;
- responsáveis e contatos;
- arquivamento lógico, desativação e restauração;
- importação e exportação;
- selectors que restringem pacientes ao profissional autorizado.

Relações recebidas pela API devem ser validadas no mesmo escopo do terapeuta. Exclusão física de pacientes com histórico clínico deve ser evitada quando a regra de retenção exigir preservação.

## `apps.records`

Responsabilidades:

- anamnese;
- evoluções clínicas e versões;
- aditivos após bloqueio de edição;
- plano terapêutico, metas e acompanhamentos;
- documentos e anexos do prontuário;
- exportações persistidas;
- confidencialidade por autor ou permissão.

Services centralizam criação, atualização, versionamento e arquivamento. Selectors aplicam autoria, confidencialidade e escopo clínico antes de retornar conteúdo.

## `apps.scheduling`

Responsabilidades:

- consultas e mudanças de status;
- recorrências;
- bloqueios e disponibilidade;
- salas físicas e telemedicina;
- pacotes de sessões;
- lembretes e recursos derivados;
- sincronização explícita com o financeiro.

Mudanças concorrentes em pacotes, recorrências e estados devem ser transacionais. O app mantém adaptação HTTP em `api/` e casos de uso em `services/`.

## `apps.financeiro`

Responsabilidades:

- transações financeiras;
- receitas, despesas e mensalidades;
- pagamentos, cancelamentos e reversões;
- filtros por período e status;
- exportações e relatórios financeiros;
- visibilidade por terapeuta e função.

Nunca confundir o financeiro operacional do terapeuta com o billing da assinatura SaaS. São domínios distintos.

## `apps.documents`

Responsabilidades:

- templates de documentos;
- biblioteca e placeholders;
- sequências numéricas concorrentes;
- geração e persistência de PDF;
- snapshot do conteúdo utilizado;
- hash de integridade;
- assinatura, arquivamento e cancelamento.

A numeração deve usar bloqueio de linha quando houver concorrência. Downloads e documentos gerados devem ser filtrados pelo proprietário antes da resolução por UUID.

## `apps.reports`

Responsabilidades:

- KPIs e gráficos de consultas;
- retenção, risco de evasão e dados demográficos;
- DRE, inadimplência, convênios e projeções;
- agendamento online;
- exportações CSV.

Selectors realizam consultas por período e proprietário. Services transformam os dados em indicadores sem misturar regras analíticas nas views.

## `apps.forms`

Responsabilidades:

- criação de templates e campos;
- publicação e desativação;
- submissões e respostas;
- validação de estrutura e tipos de campo;
- associação com paciente quando aplicável.

Respostas podem conter dados sensíveis e devem seguir o mesmo controle de acesso de pacientes e prontuários.

## `apps.billing`

Responsabilidades:

- planos e preços;
- teste gratuito e assinatura;
- checkout e ordens;
- pagamentos e parcelamento;
- cancelamento e inadimplência;
- reconciliação com o gateway;
- webhooks idempotentes;
- autenticação condicionada à situação da assinatura.

Views devem delegar ao service. A integração Asaas fica em `infrastructure/payments/asaas` ou módulo equivalente de infraestrutura.

## `apps.communications`

Responsabilidades:

- notificações internas;
- e-mail;
- templates administrativos;
- automações;
- preferências e canais;
- fila persistente e tentativas;
- links públicos com token em hash, expiração e uso único;
- webhooks de entrega quando configurados.

Destinos devem ser mascarados em respostas e protegidos em repouso quando aplicável. Templates não devem permitir variáveis clínicas arbitrárias.

## `apps.audit`

Responsabilidades:

- registrar acesso e ações sensíveis;
- preservar autor, ação, recurso, horário e metadados necessários;
- impedir alteração comum dos registros de auditoria;
- apoiar investigação e conformidade.

Auditoria não deve copiar conteúdo clínico integral, tokens, senhas, chaves ou payloads externos sensíveis.

## Dependências entre domínios

Dependências importantes devem ser explícitas:

- agenda pode solicitar sincronização com o financeiro por service dedicado;
- records e documents podem usar storage privado e exportações;
- billing usa gateway externo, mas não deve alterar o financeiro clínico;
- communications recebe eventos administrativos de outros domínios sem assumir suas regras internas;
- audit observa ações na borda ou em services sensíveis sem se tornar fonte de verdade do domínio.
