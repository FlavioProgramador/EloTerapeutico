# Relatório da refatoração documental

## Resumo executivo

A documentação foi reconstruída a partir do código, migrations, testes, configurações, workflows e estrutura frontend/backend do Elo Terapêutico. O trabalho remove afirmações não comprovadas, consolida documentos históricos e cria um portal técnico para desenvolvimento, operação, segurança e suporte.

## Base analisada

- repositório: `FlavioProgramador/EloTerapeutico`;
- branch-base: `main`;
- commit-base: `176cba63ed3edf1cee232363e5a89c4b7fda28ac`;
- data: 10/07/2026;
- branch de trabalho: `docs/refatoracao-completa`.

## Fontes analisadas

- settings `base`, `dev`, `test` e `prod`;
- URLs raiz e por módulo;
- models, serializers, views, permissions, services, actions e selectors relevantes;
- migrations/seeds identificados;
- componentes, contexts, serviços, hooks e páginas frontend;
- Dockerfiles e Docker Compose;
- requirements, package/lock e pyproject;
- workflows backend-security e frontend-ci;
- testes dos principais domínios;
- documentação anterior sob `docs/` e roadmaps duplicados.

## Documentos anteriores encontrados

Foram encontrados documentos em `docs/project`, `docs/modules`, `docs/architecture`, `docs/technical`, `docs/seguranca`, além de `docs/billing.md` e roadmaps em backend/frontend. Havia conteúdo útil, mas também nomenclatura divergente, duplicação, caminhos antigos e afirmações desatualizadas.

## Consolidações e remoções

- visão de produto/roadmaps migrados para `docs/01-visao-geral`;
- arquitetura migrada para `docs/02-arquitetura`;
- módulos antigos consolidados em `docs/05-modulos`;
- auditoria e segurança consolidadas em `docs/08-seguranca`;
- LGPD consolidada em `docs/09-lgpd`;
- contribuição consolidada em `docs/13-desenvolvimento` e `docs/14-contribuicao`;
- billing incluído como módulo, API, caso de uso e segurança;
- roadmaps de backend/frontend substituídos por ponte para a fonte central.

## Módulos documentados

Autenticação, usuários, dashboard, pacientes, prontuário, agenda, financeiro, documentos, formulários, relatórios, billing, auditoria e administração.

## Casos de uso

Foram criados casos com prefixos `UC-AUTH`, `UC-PAC`, `UC-REC`, `UC-AGE`, `UC-FIN`, `UC-DOC`, `UC-FOR`, `UC-BIL` e `UC-ADM`, além de matriz de atores, permissões, dados, riscos e status.

## Diagramas

- contexto;
- containers;
- entidade-relacionamento resumido;
- requisição/autorização;
- login;
- exportação clínica;
- webhook Asaas;
- estados do job;
- produção Azure;
- ciclo de vida LGPD;
- resposta a incidentes.

Todos usam Mermaid embutido em Markdown.

## Inconsistências encontradas

1. README antigo afirmava arquitetura SaaS multi-tenant; não há tenant/clínica explícito.
2. README referenciava `requirements/local.txt`, arquivo inexistente; o projeto usa `requirements/dev.txt`.
3. versões e estrutura indicadas não correspondiam ao código atual: Next.js 16/React 19/Django 5 e app `users`.
4. documentação antiga confundia ou fragmentava financeiro clínico e billing SaaS.
5. Redis podia ser interpretado como fila; exportações usam fila persistida no banco.
6. Azure era descrito sem separar suporte no código de implantação comprovada.
7. licença/propriedade era apresentada sem arquivo `LICENSE`.
8. havia documentos duplicados sobre pacientes, prontuário, financeiro, roadmap e contribuição.
9. raiz expunha exemplo de ambiente incompleto e referência frontend não comprovada.
10. billing está publicado em dois prefixos de URL.

## Funcionalidades parciais ou operacionais

- telemedicina depende de infraestrutura final;
- Azure Blob depende de conta/container/configuração;
- SMTP depende de credenciais;
- observabilidade depende de serviço externo;
- IA clínica aparece como indisponível quando não configurada;
- backup/restauração e retenção são operacionais;
- testes frontend não cobrem todos os módulos.

## Funcionalidades não implementadas ou não comprovadas

- tenant/clínica explícito;
- política automática global de retenção/exclusão;
- antivírus de uploads;
- MFA;
- portal completo de direitos do titular;
- deploy Azure/IaC comprovado;
- IA clínica autônoma segura/aprovada.

## Riscos documentados

- JWT em cookies acessíveis ao JavaScript;
- filesystem local permitido em produção quando a flag não é habilitada;
- auditoria fail-open e dependente de instrumentação;
- webhook sem token aceito no desenvolvimento;
- SQL Explorer/admin privilegiado;
- ausência de tenant;
- falta de antimalware;
- dependência de Asaas e processos de backup/retention.

## Comandos e checks documentados

- Django check e migrations;
- pytest e coverage;
- Ruff, mypy, Bandit e pip-audit;
- ESLint, TypeScript, teste e build Next.js;
- Docker Compose e worker;
- health check e smoke tests.

## Validações desta tarefa

- escopo funcional comparado com URLs, models e testes;
- links dos índices e navegação revisados contra a árvore criada;
- blocos Mermaid conferidos quanto a abertura/fechamento;
- exemplos revisados para não conter credenciais ou dados reais;
- alterações limitadas a documentação, templates de contribuição e exemplos de ambiente;
- nenhuma regra de negócio, migration ou código funcional alterado;
- nenhum merge ou deploy realizado.

### Limitação de execução

O ambiente de execução não disponibilizou checkout Git autenticado/`gh` nem acesso de rede do container. Por isso, suítes de runtime não foram executadas localmente nesta tarefa. Os comandos reais foram conferidos nos manifests/workflows e devem ser executados pelo CI ou por checkout local antes do merge. Esta limitação não é ocultada nem considerada aprovação dos testes.

## Estratégia de commits

1. `docs(readme): refaz apresentacao e portal da documentacao`;
2. `docs(arquitetura): documenta componentes instalacao e configuracao`;
3. `docs(modulos): documenta dominios e regras de negocio`;
4. `docs(api): documenta casos de uso endpoints e autorizacao`;
5. `docs(seguranca): consolida controles lgpd testes e operacao`;
6. `docs: adiciona contribuicao adrs e relatorio final`;
7. commit de validação/ajustes finais, quando necessário.

## Resultado

A branch fica pronta para revisão por Pull Request. Antes do merge, revisar o diff, executar CI/checks em checkout completo e confirmar especialmente permissões, variáveis e comandos do ambiente real.

Não houve merge, deploy ou alteração direta da `main`.
