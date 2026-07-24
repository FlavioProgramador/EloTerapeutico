# Status do projeto

## Revisão documentada

- **commit-base:** `75827a2dbfe7d4f86f0865f05d9a5a8f660e0f78`;
- **data da análise:** 23/07/2026;
- **branch analisada:** `main`;
- **estado:** desenvolvimento ativo e pré-produção;
- **deploy em produção:** não comprovado pelo repositório.

## Síntese

O projeto possui backend e frontend funcionais, migrations, testes, Docker Compose, PostgreSQL, Redis, Celery, quatro workers especializados, Celery Beat, integrações configuráveis e Billing com Asaas. A base funcional é ampla, mas não deve ser considerada pronta para armazenar dados clínicos reais sem infraestrutura, operação e validações de produção.

A autenticação utiliza o Next.js como BFF: access e refresh tokens ficam em cookies `HttpOnly`, métodos mutáveis usam proteção CSRF e o Django permanece responsável pela autorização. A produção configura autenticação tenant-aware e exige organização ativa.

O domínio `apps.organizations` implementa organização, memberships, papéis, convites, onboarding, configurações e perfil profissional. A principal limitação de multi-tenancy deixou de ser a ausência de tenant explícito e passou a ser a migração transversal de ownership legado e a necessidade de comprovar isolamento em todos os módulos, tasks, relatórios e integrações.

A telemedicina possui implementação de áudio e vídeo com LiveKit, convites, consentimento, E2EE, webhooks e manutenção de salas. Ela continua indisponível por padrão e depende de credenciais, HTTPS/WSS, webhook público protegido e validação em staging.

## Estado resumido

| Área | Situação | Observação |
| --- | --- | --- |
| Autenticação | ✅ / ⚠️ | Implementada; produção exige secrets, HTTPS, CSP, monitoramento e revisão contínua |
| Organizações | 🟡 | Tenant explícito presente; ownership legado ainda requer auditoria transversal |
| Pacientes | 🟡 | Cadastro e lifecycle presentes; ampliar E2E e isolamento por organização |
| Prontuário | 🟡 / ⚠️ | Fluxos amplos; retenção, storage privado e operação clínica ainda pendentes |
| Agenda | 🟡 | Consultas, recorrências, bloqueios e pacotes presentes; validar concorrência e timezone |
| Telemedicina | 🟠 / ⚠️ | LiveKit implementado; depende de configuração e staging |
| Financeiro clínico | 🟡 | Fluxos internos presentes; conciliação e ownership precisam de validação ponta a ponta |
| Documentos | 🟠 / ⚠️ | Geração e hash presentes; produção exige storage privado e política de retenção |
| Formulários | 🟡 | Construtor e submissões presentes; portal público e versionamento exigem revisão |
| Comunicações | 🟠 | Fila Celery e canais internos presentes; providers oficiais dependem de configuração |
| Relatórios | 🟡 | Agregações presentes; cobertura e métricas por tenant precisam ser ampliadas |
| Billing SaaS | 🟠 | Asaas, checkout, webhooks e reconciliação presentes; credenciais e staging pendentes |
| Auditoria | 🟡 | Trilha sanitizada presente; revisar retenção e cobertura fora da ORM |
| Administração | ✅ / ⚠️ | Django Unfold presente; permissões operacionais precisam ser revisadas |
| Portal do paciente | 🔴 | Não implementado como domínio completo |
| Inteligência artificial | 📌 | Planejada; sem provedor ou fluxo funcional |

## Infraestrutura atual

O Compose local contém:

- `db`;
- `redis`;
- `backend`;
- `frontend`;
- `celery-worker-default`;
- `celery-worker-exports`;
- `celery-worker-uploads`;
- `celery-worker-communications`;
- `celery-beat`.

O Compose usa `runserver`, `next dev` e volumes de código, portanto representa desenvolvimento e validação local. Produção deve usar imagens imutáveis, Gunicorn, `next start`, serviços gerenciados ou protegidos, secrets, HTTPS, storage privado, backup e observabilidade.

## Integrações

| Integração | Situação |
| --- | --- |
| Asaas | implementação presente; requer credenciais, webhook e staging |
| LiveKit | implementação presente; desativada por padrão |
| Azure Blob | configurável; infraestrutura implantada não é comprovada |
| SMTP/SendGrid | configurável; desenvolvimento usa console |
| WhatsApp manual | implementado por link e confirmação humana |
| WhatsApp Business | interface preparada; provider oficial não comprovado |
| SMS | interface preparada; provider não definido |
| IA | não implementada |

## Requisitos antes de dados reais

- HTTPS, domínio e proxy confiável;
- secrets fortes e distintos;
- PostgreSQL e Redis protegidos;
- storage privado persistente;
- backup e restauração testados;
- monitoramento, alertas e runbooks;
- validação das integrações em staging;
- teste de isolamento com múltiplas organizações;
- revisão de permissões do Admin;
- política de retenção e descarte;
- avaliação jurídica, LGPD e contratos com operadores externos.

## Referências

- [Matriz de módulos](matriz-de-modulos.md)
- [Matriz de integrações](matriz-de-integracoes.md)
- [Matriz de containers](matriz-de-containers.md)
- [Inventário tecnológico](inventario-tecnologico.md)
- [Auditoria do backlog](auditoria-backlog.md)
- [Limitações conhecidas](../01-visao-geral/limitacoes.md)

## Critério de atualização

Este arquivo deve ser revisto quando houver mudança relevante em arquitetura, módulos, segurança, dependências, containers, integrações, ambiente de produção ou modelo de propriedade dos dados.

[Voltar](README.md)
