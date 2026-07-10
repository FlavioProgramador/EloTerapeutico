# Documentação do Elo Terapêutico

Este diretório é o portal técnico oficial do projeto. A documentação foi revisada a partir do código no commit-base `176cba63ed3edf1cee232363e5a89c4b7fda28ac`, em 10 de julho de 2026.

## Legenda de situação

- ✅ Implementado e documentado
- 🟡 Parcialmente implementado
- 🔴 Não implementado
- ⚠️ Requer configuração operacional
- 📌 Planejado

## Como navegar

| Seção | Público principal | Conteúdo |
| --- | --- | --- |
| [01 — Visão geral](01-visao-geral/README.md) | Produto, suporte e novos colaboradores | Produto, escopo, situação e limitações |
| [02 — Arquitetura](02-arquitetura/README.md) | Engenharia e arquitetura | Backend, frontend, banco, integrações e diagramas |
| [03 — Instalação](03-instalacao/README.md) | Desenvolvimento e suporte | Execução local, Docker e verificação |
| [04 — Configuração](04-configuracao/README.md) | DevOps e desenvolvimento | Ambientes e variáveis de ambiente |
| [05 — Módulos](05-modulos/README.md) | Produto e engenharia | Regras, modelos, API, interface e segurança por domínio |
| [06 — Casos de uso](06-casos-de-uso/README.md) | Produto, QA e engenharia | Atores, fluxos e matriz de permissões |
| [07 — API](07-api/README.md) | Backend, frontend e integrações | Convenções, autenticação, erros e endpoints |
| [08 — Segurança](08-seguranca/README.md) | Segurança, DevOps e engenharia | Controles, ameaças, riscos e checklist de produção |
| [09 — LGPD](09-lgpd/README.md) | Operação, produto e privacidade | Mapeamento técnico do tratamento de dados |
| [10 — Testes](10-testes/README.md) | Engenharia e QA | Estratégia, comandos e CI |
| [11 — Deploy](11-deploy/README.md) | DevOps | Produção, Azure, rollback e pós-deploy |
| [12 — Operação](12-operacao/README.md) | Suporte e SRE | Logs, health checks, backup e falhas |
| [13 — Desenvolvimento](13-desenvolvimento/README.md) | Colaboradores | Branches, commits, padrões e revisão |
| [14 — Contribuição](14-contribuicao/README.md) | Comunidade e equipe | Regras de contribuição e checklist de PR |
| [15 — Suporte](15-suporte/README.md) | Suporte e desenvolvimento | Diagnóstico e problemas comuns |
| [16 — ADRs](16-decisoes-arquiteturais/README.md) | Arquitetura e engenharia | Decisões verificadas na implementação |
| [17 — Referência](17-referencia/README.md) | Todos | Glossário, matrizes, comandos e status |

## Situação da documentação

| Área | Situação | Observação |
| --- | --- | --- |
| Visão geral | ✅ | Alinhada ao código-base analisado |
| Arquitetura | ✅ | Inclui diagramas Mermaid e limites comprovados |
| Instalação e configuração | ✅ | Comandos derivados dos arquivos reais |
| Módulos e API | ✅ | Organizados por domínio implementado |
| Segurança | ✅ | Separa controles implementados, operacionais e pendentes |
| LGPD | ✅ | Descrição técnica; não substitui avaliação jurídica |
| Deploy e operação | 🟡 | O repositório oferece configuração, mas não prova ambiente implantado |
| Observabilidade | 🟡 | Logging estruturado existe; serviço externo não é comprovado |
| Backup e restauração | ⚠️ | Exigem processo operacional fora do código |
| Multi-tenancy por clínica | 🔴 | Não há tenant/clínica explícito no modelo atual |

## Convenções

- Português do Brasil;
- nomes oficiais de tecnologias permanecem em inglês;
- rotas são apresentadas com o prefixo `/api/v1/`;
- exemplos usam dados evidentemente fictícios;
- afirmações importantes incluem referências ao caminho do código quando útil;
- `Status: parcialmente implementado` sinaliza implementação incompleta;
- `Status: planejado ou não implementado` sinaliza ausência comprovada.

## Fonte da verdade

A ordem de precedência é:

1. código, migrations e testes do commit analisado;
2. configurações e workflows do repositório;
3. esta documentação;
4. documentos históricos, quando ainda existirem.

Em caso de divergência, abra uma issue e corrija o documento no mesmo Pull Request da mudança funcional.

## Revisão

- **Data:** 10/07/2026
- **Commit analisado:** `176cba63ed3edf1cee232363e5a89c4b7fda28ac`
- **Relatório:** [RELATORIO_DA_REFATORACAO.md](RELATORIO_DA_REFATORACAO.md)
