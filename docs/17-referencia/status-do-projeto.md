# Status do projeto

## Revisão documentada

- commit-base: `807ddb96b79d2cb89ae84ca10cb615e1b969c1c1`;
- data da análise: 20/07/2026;
- branch de estabilização: `agent/estabiliza-autenticacao-ci`;
- estado: desenvolvimento ativo e pré-produção;
- deploy em produção: não comprovado pelo repositório.

## Síntese

O projeto possui backend e frontend funcionais, migrations, testes, Docker Compose, PostgreSQL, Redis, Celery, workers especializados, integrações configuráveis e billing com Asaas. A base funcional é ampla, mas não deve ser considerada pronta para armazenar dados clínicos reais sem infraestrutura, operação e validações de produção.

A autenticação utiliza o Next.js como BFF: access e refresh tokens são mantidos em cookies `HttpOnly`, o cookie CSRF é usado em double-submit e o Django permanece responsável pela autorização. A revisão de estabilização acrescenta respostas de gateway sanitizadas, testes unitários e E2E de login, CSRF, refresh e logout, além de PostgreSQL e gates obrigatórios de Ruff/mypy no CI.

A principal restrição arquitetural continua sendo a ausência de tenant/clínica explícito. Há isolamento por terapeuta em diversos domínios, mas isso não representa multi-tenancy completo.

## Estado resumido

- autenticação: implementada, com validação adicional pendente nos workflows do PR;
- módulos administrativos e clínicos: amplos, porém com maturidade desigual;
- telemedicina: sala lógica e acesso implementados, sem mídia em tempo real;
- IA: planejada, sem integração funcional;
- integrações externas: dependentes de credenciais e staging;
- produção: exige storage privado, backup/restauração, observabilidade, alertas e runbooks.

## Referências

- [Matriz de módulos](matriz-de-modulos.md)
- [Matriz de integrações](matriz-de-integracoes.md)
- [Auditoria do backlog](auditoria-backlog.md)
- [Limitações conhecidas](../01-visao-geral/limitacoes.md)

## Critério de atualização

Este arquivo deve ser revisto quando houver mudança relevante em arquitetura, módulos, segurança, ambiente de produção ou modelo de propriedade dos dados.

[Voltar](README.md)
