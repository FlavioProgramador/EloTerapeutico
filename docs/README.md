# Documentação do Elo Terapêutico

Este diretório é o portal técnico, funcional, arquitetural e operacional oficial do projeto. A revisão atual foi realizada contra a branch `main`, no commit `75827a2dbfe7d4f86f0865f05d9a5a8f660e0f78`, em 23 de julho de 2026.

## Fonte da verdade

A ordem de precedência documental é:

1. código atual;
2. migrations;
3. testes automatizados;
4. configurações, Docker e workflows;
5. arquivos de dependências;
6. documentação atual;
7. relatórios históricos.

Relatórios anteriores registram o estado do projeto no momento em que foram produzidos. Eles não substituem esta documentação quando houver divergência.

## Legenda de situação

- ✅ **Implementado e validado:** fluxo principal existe e possui validação automatizada relevante;
- 🟡 **Implementado parcialmente:** existem camadas funcionais, mas faltam fluxos, cobertura ou regras importantes;
- 🟠 **Implementado, depende de integração/configuração:** código existe, porém operação depende de credenciais, provedor ou infraestrutura;
- 🔴 **Não implementado:** não existe fluxo funcional completo;
- ⚠️ **Não pronto para produção:** controles operacionais, segurança ou infraestrutura ainda impedem uso com dados reais;
- 📌 **Planejado:** intenção de produto sem implementação funcional comprovada.

## Como navegar

| Seção | Público principal | Conteúdo |
| --- | --- | --- |
| [Backend](backend/README.md) | Backend, QA, segurança e DevOps | Arquitetura, apps, API, autenticação, workers e configuração |
| [01 — Visão geral](01-visao-geral/README.md) | Produto, suporte e novos colaboradores | Produto, escopo, situação e limitações |
| [02 — Arquitetura](02-arquitetura/README.md) | Engenharia e arquitetura | Backend, frontend, dados, BFF, integrações, filas e diagramas |
| [03 — Instalação](03-instalacao/README.md) | Desenvolvimento e suporte | Execução local, Docker e verificação |
| [04 — Configuração](04-configuracao/README.md) | DevOps e desenvolvimento | Ambientes, variáveis, secrets e Docker |
| [05 — Módulos](05-modulos/README.md) | Produto e engenharia | Finalidade, regras, API, interface, segurança, testes e limitações por domínio |
| [06 — Casos de uso](06-casos-de-uso/README.md) | Produto, QA e engenharia | Atores, fluxos e matriz de permissões |
| [07 — API](07-api/README.md) | Backend, frontend e integrações | Convenções, autenticação, erros e endpoints |
| [08 — Segurança](08-seguranca/README.md) | Segurança, DevOps e engenharia | Controles, ameaças, riscos e checklist de produção |
| [09 — LGPD](09-lgpd/README.md) | Operação, produto e privacidade | Mapeamento técnico do tratamento de dados |
| [10 — Testes](10-testes/README.md) | Engenharia e QA | Estratégia, comandos, E2E e CI |
| [11 — Deploy](11-deploy/README.md) | DevOps | Arquitetura suportada, Azure, rollback e pós-deploy |
| [12 — Operação](12-operacao/README.md) | Suporte e SRE | Logs, health checks, workers, backup e falhas |
| [13 — Desenvolvimento](13-desenvolvimento/README.md) | Colaboradores | Branches, commits, arquitetura e revisão |
| [14 — Contribuição](14-contribuicao/README.md) | Comunidade e equipe | Regras de contribuição e checklist de PR |
| [15 — Suporte](15-suporte/README.md) | Suporte e desenvolvimento | Diagnóstico e problemas comuns |
| [16 — ADRs](16-decisoes-arquiteturais/README.md) | Arquitetura e engenharia | Decisões verificadas na implementação |
| [17 — Referência](17-referencia/README.md) | Todos | Status, matrizes, inventário, comandos e glossário |

## Referências rápidas

- [Status atual do projeto](17-referencia/status-do-projeto.md)
- [Matriz de módulos](17-referencia/matriz-de-modulos.md)
- [Matriz de integrações](17-referencia/matriz-de-integracoes.md)
- [Matriz de containers](17-referencia/matriz-de-containers.md)
- [Inventário tecnológico](17-referencia/inventario-tecnologico.md)
- [Variáveis de ambiente](04-configuracao/variaveis-de-ambiente.md)
- [Filas e processamento assíncrono](02-arquitetura/filas-e-processamento-assincrono.md)
- [Instalação com Docker](03-instalacao/instalacao-docker.md)
- [Organizações e multi-tenancy](05-modulos/organizacoes/README.md)
- [Comunicações](05-modulos/comunicacoes/README.md)
- [Telemedicina](05-modulos/telemedicina/README.md)

## Situação da documentação

| Área | Situação | Observação |
| --- | --- | --- |
| Visão geral | ✅ | README e portal alinhados ao commit analisado |
| Arquitetura | ✅ | Inclui BFF, tenant, Redis, quatro filas Celery e integrações |
| Instalação e Docker | ✅ | Serviços, comandos, volumes e diferenças entre dev/prod documentados |
| Configuração | ✅ | Escopo dos três arquivos `.env.example` e variáveis por componente |
| Módulos | 🟡 | Domínios principais documentados; maturidade varia por módulo |
| API | ✅ | Prefixos e contratos principais derivados das rotas atuais |
| Segurança e LGPD | 🟡 | Controles técnicos documentados; conformidade jurídica não é presumida |
| Deploy e operação | 🟡 | Repositório oferece configuração e runbooks; ambiente implantado não é comprovado |
| Observabilidade | 🟡 | Logging estruturado existe em produção; serviço externo não é comprovado |
| Backup e restauração | ⚠️ | Exigem processo operacional testado fora do código |
| Multi-tenancy | 🟡 | Organização e membership existem; ownership legado ainda requer revisão transversal |
| Integrações externas | 🟠 | Dependem de credenciais, provedores e validação em staging |

## Convenções

- português do Brasil;
- nomes oficiais de tecnologias permanecem em inglês;
- rotas autenticadas usam, em regra, o prefixo `/api/v1/`;
- exemplos usam dados fictícios e placeholders;
- status de implementação deve apontar para evidência no código, testes ou configuração;
- frontend não é fronteira de autorização;
- feature flag não equivale a integração operacional;
- documentos históricos devem ser identificados como históricos;
- mudanças funcionais devem atualizar a documentação relacionada no mesmo Pull Request.

## Validação automática

Execute na raiz:

```bash
python scripts/validate_docs.py
docker compose config
docker compose config --services
```

O workflow `.github/workflows/docs-validation.yml` valida links locais, cercas Markdown, padrões de segredo, referências canônicas e sincronização de itens estruturais da documentação.

## Revisão

- **Data:** 23/07/2026;
- **Branch analisada:** `main`;
- **Commit-base:** `75827a2dbfe7d4f86f0865f05d9a5a8f660e0f78`;
- **Escopo:** documentação técnica, funcional, arquitetural e operacional;
- **Relatório desta revisão:** [Relatório da refatoração documental](17-referencia/relatorio-refatoracao-documental-2026-07-23.md).
