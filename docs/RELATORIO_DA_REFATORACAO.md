# Relatório da refatoração documental

## Resumo executivo

A documentação do Elo Terapêutico foi reconstruída a partir do código, migrations, testes, configurações, workflows e estrutura real do frontend e backend. O trabalho remove afirmações não comprovadas, consolida documentos históricos e cria um portal técnico para desenvolvimento, produto, segurança, privacidade, implantação, operação e suporte.

A alteração foi realizada em branch própria e submetida como Pull Request em rascunho. Nenhuma regra de negócio, migration ou implementação funcional foi alterada.

## Base analisada

- **Repositório:** `FlavioProgramador/EloTerapeutico`
- **Branch-base:** `main`
- **Commit-base:** `176cba63ed3edf1cee232363e5a89c4b7fda28ac`
- **Data da análise:** 10/07/2026
- **Branch de trabalho:** `docs/refatoracao-completa`
- **Pull Request:** `#137`, aberto como rascunho

## Escopo final do diff

| Situação | Quantidade |
| --- | ---: |
| Arquivos adicionados | 132 |
| Arquivos atualizados | 5 |
| Arquivos removidos/consolidados | 22 |
| **Total de arquivos alterados** | **159** |

As alterações estão limitadas a:

- `README.md`;
- `docs/`;
- exemplos de ambiente;
- template de Pull Request;
- workflow e script de validação documental;
- arquivos de roadmap convertidos em pontes para a fonte central.

Não foram alterados models, serializers, views, services, componentes funcionais, migrations, dependências ou infraestrutura de produção.

## Estrutura documental criada

```text
README.md

docs/
├── README.md
├── RELATORIO_DA_REFATORACAO.md
├── 01-visao-geral/
├── 02-arquitetura/
├── 03-instalacao/
├── 04-configuracao/
├── 05-modulos/
├── 06-casos-de-uso/
├── 07-api/
├── 08-seguranca/
├── 09-lgpd/
├── 10-testes/
├── 11-deploy/
├── 12-operacao/
├── 13-desenvolvimento/
├── 14-contribuicao/
├── 15-suporte/
├── 16-decisoes-arquiteturais/
└── 17-referencia/
```

## Fontes analisadas

- settings Django `base`, `dev`, `test` e `prod`;
- URLs raiz e por módulo;
- models e migrations;
- serializers, views, permissions, services, actions e selectors relevantes;
- componentes, contexts, serviços, hooks e páginas do frontend;
- Dockerfiles e Docker Compose;
- requirements, `package.json`, lockfile e `pyproject.toml`;
- workflows de CI, segurança, dependências, imagens e CodeQL;
- testes dos principais domínios;
- documentos anteriores sob `docs/` e roadmaps do backend/frontend.

## Módulos documentados

1. autenticação;
2. usuários;
3. dashboard;
4. pacientes;
5. prontuário;
6. agenda;
7. financeiro clínico;
8. documentos;
9. formulários;
10. relatórios;
11. billing e assinatura SaaS;
12. auditoria;
13. administração Django/Unfold.

## Casos de uso criados

Foram documentados casos com os prefixos:

- `UC-AUTH` — autenticação e recuperação;
- `UC-PAC` — pacientes;
- `UC-REC` — prontuário e exportação;
- `UC-AGE` — agenda e telemedicina;
- `UC-FIN` — financeiro;
- `UC-DOC` — documentos;
- `UC-FOR` — formulários;
- `UC-BIL` — billing;
- `UC-ADM` — administração.

Também foi criada uma matriz de atores, permissões, dados acessados, riscos e situação de implementação.

## Diagramas Mermaid criados

- contexto;
- containers;
- entidade-relacionamento resumido;
- fluxo de requisição e autorização;
- login;
- exportação clínica;
- webhook Asaas;
- estados da fila de exportação;
- arquitetura de produção;
- ciclo de vida de dados;
- resposta a incidentes.

## Documentos anteriores encontrados e consolidados

Foram encontrados documentos em:

- `docs/project/`;
- `docs/modules/`;
- `docs/architecture/`;
- `docs/technical/`;
- `docs/seguranca/`;
- `docs/billing.md`;
- roadmaps no backend e frontend.

Havia conteúdo útil, mas também duplicação, nomenclatura divergente, caminhos antigos e afirmações desatualizadas. Vinte e dois arquivos legados foram removidos após a consolidação. Os roadmaps de backend e frontend foram mantidos como pontes curtas para evitar links históricos quebrados.

## Inconsistências encontradas

1. O README anterior afirmava arquitetura SaaS multi-tenant pronta, mas não existe entidade explícita de clínica/tenant.
2. O comando anterior usava `requirements/local.txt`, arquivo inexistente; o projeto usa `requirements/dev.txt`.
3. Versões e estrutura documentadas não correspondiam ao código atual: Next.js 16, React 19, Node 24, Django 5 e app `users`.
4. Financeiro clínico e billing SaaS estavam fragmentados ou podiam ser confundidos.
5. Redis podia ser interpretado como fila; exportações clínicas usam fila persistida no banco.
6. Azure era apresentado sem separar suporte no código de implantação comprovada.
7. Licenciamento era sugerido sem existir arquivo `LICENSE` no commit-base.
8. Havia documentação duplicada sobre pacientes, prontuário, financeiro, roadmap e contribuição.
9. Exemplos de ambiente estavam incompletos e não representavam todas as variáveis relevantes.
10. Billing está publicado em dois prefixos: `/api/v1/billing/` e `/api/billing/`.

## Funcionalidades parcialmente implementadas ou operacionais

- telemedicina depende da infraestrutura audiovisual e validação final do ambiente;
- Azure Blob depende de conta, container privado e configuração;
- SMTP depende de credenciais e entrega operacional;
- observabilidade depende de serviço externo;
- IA clínica aparece como indisponível quando não configurada;
- backup, restauração e retenção dependem de processo operacional;
- testes frontend não cobrem todos os módulos;
- enforcement dos recursos de plano precisa permanecer consistente em todos os domínios.

## Funcionalidades não implementadas ou não comprovadas

- tenant/clínica explícito e isolamento multi-clínica completo;
- política automática global de retenção e exclusão;
- análise antimalware dos uploads;
- MFA;
- portal completo de direitos do titular;
- infraestrutura Azure criada por IaC e implantação comprovada;
- IA clínica autônoma segura, aprovada e configurada.

## Riscos residuais documentados

- JWT armazenado em cookies acessíveis ao JavaScript;
- filesystem local permitido em produção quando a flag de storage privado não é habilitada;
- auditoria fail-open e dependente de instrumentação por endpoint;
- webhook Asaas sem token aceito apenas no ambiente de desenvolvimento;
- acesso privilegiado pelo Django Admin e SQL Explorer;
- ausência de tenant explícito;
- falta de antimalware;
- retenção, backup e restauração fora do código;
- dependência operacional do Asaas, SMTP, Redis e Azure.

## Validações automatizadas

Foi adicionado `scripts/validate_docs.py`, executado pelo workflow `Documentation Validation`.

Resultado da execução no commit `bcbafdd23d9ff038949497180e906280e858a7f9`:

```text
Documentação validada: 166 arquivos Markdown, links locais existentes,
cercas balanceadas e nenhum padrão de segredo detectado.
```

O validador verifica:

- links Markdown relativos;
- existência dos destinos;
- cercas de código e Mermaid balanceadas;
- links que escapam da raiz;
- padrões comuns de tokens;
- valores suspeitos em variáveis sensíveis dos exemplos `.env`.

O workflow publica o relatório como artefato mesmo em caso de falha, facilitando diagnóstico.

## Testes e checks

Comandos reais foram conferidos nos manifests e workflows:

### Backend

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest --create-db
ruff check .
mypy .
bandit -r apps infrastructure config -c pyproject.toml
pip-audit -r requirements/base.txt
```

### Frontend

```bash
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

### Limitação do ambiente do agente

O ambiente local do agente não possuía checkout autenticado nem resolução de rede para baixar o repositório diretamente. Por isso, as suítes de runtime não foram executadas localmente. O Pull Request disparou os workflows reais do repositório, e seus resultados devem ser usados como fonte de verdade antes do merge.

Essa limitação não é tratada como aprovação dos testes e foi registrada de forma explícita.

## Commits da branch

1. `5b413ceb1f9ee592c9ef6ec559f3eb595a85db11` — `docs(readme): refaz apresentacao e portal da documentacao`
2. `427556b0378f86512ad00e523a35a26237c0d547` — `docs(arquitetura): documenta componentes instalacao e configuracao`
3. `14b1a3223b00abb14a68598e547eff4455ca75fe` — `docs(modulos): documenta dominios e regras de negocio`
4. `2f41652db6b7dee284741325d3cd37901857713d` — `docs(api): documenta casos de uso endpoints e autorizacao`
5. `9a7714ac854cd4a1bc5d1d279f58fbeda145845e` — `docs(seguranca): consolida controles lgpd testes e operacao`
6. `80d27ef89aeda2a06cace788cde74abefcdf70ad` — `docs: adiciona contribuicao adrs e relatorio final`
7. `829f2049171ca4d6f7d02940ed38c34294f8ddab` — `ci(docs): adiciona validacao automatica da documentacao`
8. `a12468e5b11622b0dc8caa5d42c49574c2bd1a10` — `ci(docs): reduz ruido da validacao no workflow`
9. `0afcd62dc66203153702730d209eb95c77cd5bf0` — `ci(docs): publica relatorio da validacao como artefato`
10. `bcbafdd23d9ff038949497180e906280e858a7f9` — `fix(docs): corrige deteccao de variaveis vazias`
11. commit atual — `docs: registra validacoes e resultado final`

## Instruções para revisão

1. revisar o novo `README.md` e `docs/README.md`;
2. conferir especialmente escopo, matriz de módulos e limitações;
3. revisar permissões e segurança com responsáveis técnicos;
4. validar comandos no ambiente de desenvolvimento usado pela equipe;
5. conferir todos os checks do Pull Request;
6. manter o PR em rascunho enquanto houver check pendente ou falhando;
7. não fazer merge sem aprovação do conteúdo, CI e riscos residuais.

## Confirmações finais

- branch criada a partir da `main` sem alterar diretamente a branch protegida;
- documentação implementada efetivamente, não apenas planejada;
- documentos duplicados consolidados;
- exemplos sem credenciais ou dados clínicos reais;
- validação documental automatizada aprovada;
- nenhum merge realizado;
- nenhum deploy realizado;
- nenhuma publicação em produção realizada.
