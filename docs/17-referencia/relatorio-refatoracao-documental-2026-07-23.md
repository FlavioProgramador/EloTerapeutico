# Relatório da refatoração documental — 23/07/2026

## Identificação

- **Projeto:** Elo Terapêutico;
- **Repositório:** `FlavioProgramador/EloTerapeutico`;
- **Branch de implementação:** `agent/refatoracao-documentacao-completa`;
- **Branch-base analisada:** `main`;
- **Commit-base:** `75827a2dbfe7d4f86f0865f05d9a5a8f660e0f78`;
- **Data da auditoria:** 23/07/2026;
- **Escopo:** documentação técnica, funcional, arquitetural e operacional;
- **Alteração funcional intencional:** nenhuma.

## Objetivo

Atualizar a documentação usando código, migrations, testes, configurações, Docker, workflows e dependências como fontes de verdade, corrigindo referências históricas que já não representavam a arquitetura atual.

## Áreas analisadas

- README e portal `docs/`;
- Docker Compose, Dockerfiles, volumes e health checks;
- settings Django de desenvolvimento e produção;
- rotas da API;
- configuração Redis e Celery;
- apps Django e módulos frontend;
- dependências backend e frontend;
- arquivos de ambiente;
- workflows do GitHub Actions;
- integrações externas;
- segurança, LGPD, operação e deploy.

## Arquivos criados

- `docs/17-referencia/matriz-de-containers.md`;
- `docs/17-referencia/inventario-tecnologico.md`;
- `docs/12-operacao/docker-e-workers.md`;
- este relatório.

## Arquivos principais atualizados

- `README.md`;
- `docs/README.md`;
- `docs/02-arquitetura/README.md`;
- `docs/02-arquitetura/filas-e-processamento-assincrono.md`;
- `docs/02-arquitetura/integracoes.md`;
- `docs/03-instalacao/instalacao-docker.md`;
- `docs/04-configuracao/variaveis-de-ambiente.md`;
- `docs/05-modulos/README.md`;
- `docs/05-modulos/organizacoes/README.md`;
- `docs/05-modulos/comunicacoes/README.md`;
- `docs/05-modulos/comunicacoes/diagnostico-runtime.md`;
- `docs/07-api/README.md`;
- `docs/11-deploy/arquitetura-de-producao.md`;
- `docs/12-operacao/README.md`;
- `docs/17-referencia/README.md`;
- `docs/17-referencia/status-do-projeto.md`;
- `docs/17-referencia/matriz-de-modulos.md`;
- `docs/17-referencia/matriz-de-integracoes.md`;
- `.env.example`;
- `scripts/validate_docs.py`;
- `.github/workflows/docs-validation.yml`.

## Documentos consolidados por compatibilidade

Os documentos abaixo permanecem em seus caminhos antigos para preservar links, mas apontam para as páginas canônicas atuais:

- `docs/backend/asynchronous-tasks.md`;
- `docs/backend/testing-and-troubleshooting.md`.

Nenhum documento histórico foi removido sem análise de referências.

## Divergências corrigidas

### Commit e data de revisão

Documentos canônicos ainda indicavam commits e datas anteriores. README, portal e status passaram a usar o commit-base atual da auditoria.

### Multi-tenancy

A documentação afirmava que o projeto não possuía tenant explícito. O código atual contém `apps.organizations`, organizações, memberships, papéis, convites, onboarding, configurações, perfil profissional e autenticação tenant-aware em produção.

A limitação atual foi registrada corretamente: ownership legado ainda precisa ser auditado transversalmente em apps, tasks, caches, relatórios, exports e integrações.

### Telemedicina

O status antigo indicava ausência de mídia em tempo real. O código atual utiliza LiveKit para áudio e vídeo, além de tokens, convites, consentimento, E2EE, webhooks e manutenção de salas.

A documentação também registra que a integração permanece desativada por padrão e depende de HTTPS/WSS, credenciais, webhook e staging.

### Docker

Foram documentados os nove serviços atuais:

1. `db`;
2. `redis`;
3. `backend`;
4. `frontend`;
5. `celery-worker-default`;
6. `celery-worker-exports`;
7. `celery-worker-uploads`;
8. `celery-worker-communications`;
9. `celery-beat`.

Comandos que usavam `worker`, `communications-worker` ou `communications-scheduler` foram substituídos ou mantidos apenas como referência histórica explicitamente identificada.

### Celery e Redis

Documentos antigos indicavam que os fluxos não dependiam de Celery ou Redis. A documentação atual descreve Redis como broker/result backend e as filas `default`, `exports`, `uploads` e `communications`.

O schedule completo do Celery Beat foi documentado com task, frequência padrão, fila e finalidade.

### Worker de uploads

O worker `celery-worker-uploads`, anteriormente omitido em resumos, passou a ser documentado. A documentação diferencia o pipeline de verificação implementado de um provider antimalware externo, que não deve ser presumido como operacional.

### Desenvolvimento e produção

Foi explicitada a diferença entre:

- Dockerfile backend com Gunicorn e Compose com `runserver`;
- Dockerfile frontend com `next start` e Compose com `next dev`;
- imagem imutável e bind mount local;
- banco/Redis locais e serviços protegidos de produção;
- arquivo `.env` local e secret manager.

### Tecnologias

O inventário passou a incluir dependências compartilhadas e específicas de produção, como WhiteNoise, Structlog, `django-health-check` e `django-storages[azure]`, além das versões frontend, runtimes, testes e workflows.

### Variáveis de ambiente

Foram diferenciados os escopos de:

- `.env.example`;
- `backend/.env.example`;
- `frontend/.env.example`;
- `.env`;
- `backend/.env`;
- `frontend/.env.local`.

O `.env.example` da raiz foi sincronizado com variáveis já utilizadas pelo código:

- `CELERY_UPLOADS_CONCURRENCY`;
- `CLINICAL_SCAN_DISPATCH_INTERVAL_SECONDS`;
- `CLINICAL_SCAN_RECOVERY_INTERVAL_SECONDS`.

### Integrações externas

As integrações foram classificadas em interface preparada, implementação presente, configuração e validação operacional. Asaas, LiveKit, Azure Blob, SMTP, WhatsApp Business e SMS não são apresentados como operacionais sem staging.

### API

A referência passou a listar os prefixos atuais, documentação OpenAPI, health checks, BFF, autenticação e contexto de organização.

### Operação e deploy

Foi criado um runbook para backend, frontend, PostgreSQL, Redis, workers, Beat, storage, Asaas, LiveKit, SMTP e Comunicações. A arquitetura de produção passou a representar quatro workers e um Beat único, sem afirmar que o Azure já está implantado.

## Validação automática ampliada

`scripts/validate_docs.py` passou a verificar:

- links locais;
- cercas Markdown;
- padrões de segredo e token;
- existência dos documentos canônicos;
- serviços do Docker Compose na matriz de containers;
- comandos Markdown que usam serviços Docker inexistentes;
- apps Django na matriz de módulos;
- prefixos de API na referência;
- variáveis dos três arquivos de exemplo;
- versões de dependências e imagens no inventário tecnológico;
- consistência do commit-base entre documentos canônicos.

A implementação usa JSON e AST da biblioteca padrão para fontes estruturadas. O parser local do Compose é limitado à seção top-level `services`; a validação autoritativa do YAML ocorre pelo Docker Compose no CI.

## Workflow documental

`.github/workflows/docs-validation.yml` agora executa:

```bash
python3 scripts/validate_docs.py
docker compose config --quiet
docker compose config --services
```

Também observa alterações em Dockerfiles, Compose, settings, rotas, requirements, `package.json` e arquivos de ambiente que podem tornar a documentação obsoleta.

## Validação realizada

| Comando ou verificação | Resultado | Observação |
| --- | --- | --- |
| Inspeção pelo conector GitHub | Executada | Código, configurações e documentos foram lidos diretamente da branch-base |
| Revisão do diff do Pull Request | Executada parcialmente | Arquivos alterados e patch da validação foram inspecionados pelo conector |
| `python scripts/validate_docs.py` local | Não executado localmente | O ambiente do agente não conseguiu resolver `github.com` para criar checkout local |
| `docker compose config` local | Não executado localmente | Sem checkout local completo |
| GitHub Actions | Em execução no momento deste relatório | O workflow documental é a validação autoritativa desta revisão |

Nenhum comando é apresentado como aprovado antes da conclusão do respectivo workflow.

## Riscos restantes

- documentos não canônicos podem ainda conter contexto histórico; devem permanecer identificados como compatibilidade ou histórico;
- a validação documental reduz divergências, mas não substitui revisão técnica humana;
- links externos não são verificados pelo script;
- o parser local de serviços não substitui `docker compose config`;
- maturidade de módulos e produção depende de testes, infraestrutura e staging;
- multi-tenancy ainda exige auditoria de ownership em todos os domínios;
- providers externos continuam dependentes de credenciais e validação operacional.

## Critérios de manutenção

Uma mudança deve atualizar a documentação no mesmo Pull Request quando alterar:

- app Django ou feature frontend;
- rota de API;
- variável de ambiente;
- dependência ou runtime;
- Dockerfile, serviço, volume ou health check;
- fila, task ou schedule Celery;
- integração externa;
- regra de autenticação, autorização ou tenant;
- requisito de segurança, operação ou deploy.

[Voltar à referência](README.md)
