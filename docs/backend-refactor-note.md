# Arquitetura do backend — Elo Terapêutico

## Objetivo

Este documento define o padrão de organização do backend Django e registra as decisões adotadas durante a refatoração arquitetural iniciada na branch `refactor/backend-django-expert`.

A arquitetura deve preservar:

- migrations e labels dos apps existentes;
- contratos públicos da API `/api/v1/`;
- isolamento entre usuários, terapeutas e pacientes;
- rastreabilidade de dados clínicos;
- compatibilidade com o frontend Next.js;
- execução em desenvolvimento, testes e produção.

## Estrutura atual preservada

```text
backend/
├── manage.py
├── requirements/
├── elo_terapeutico/
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       ├── test.py
│       └── prod.py
├── apps/
│   ├── users/
│   ├── patients/
│   ├── records/
│   ├── agenda/
│   └── financeiro/
├── core/
└── tests/
```

Os nomes dos apps foram mantidos porque já existem migrations e tabelas associadas. Renomear `records`, `agenda`, `patients`, `users` ou `financeiro` exigiria uma migração de estado e banco desnecessariamente arriscada.

## Estrutura interna recomendada para novos módulos

Novas funcionalidades devem seguir organização por domínio:

```text
apps/<dominio>/
├── apps.py
├── admin.py
├── models.py
├── api/
│   ├── serializers.py
│   ├── permissions.py
│   ├── filters.py
│   ├── views.py
│   └── urls.py
├── services/
├── selectors/
├── validators.py
├── tasks.py
├── migrations/
└── tests/
```

Crie somente arquivos com responsabilidade real. Não crie `services`, `selectors`, `tasks` ou `validators` vazios apenas para reproduzir uma árvore idealizada.

## Responsabilidades

### `elo_terapeutico/settings`

- `base.py`: configurações compartilhadas;
- `dev.py`: desenvolvimento local;
- `test.py`: testes determinísticos e rápidos;
- `prod.py`: segurança, proxy reverso, banco, storage, logging e e-mail de produção.

### `core`

Somente código realmente compartilhado por vários domínios:

- paginação;
- tratamento global de exceções;
- auditoria;
- validações compartilhadas;
- campos reutilizáveis.

`core` não deve se transformar em depósito para regras específicas de pacientes, prontuários, agenda ou financeiro.

### `api`

A camada HTTP deve conter apenas adaptação entre requisição/resposta e domínio:

- serializers;
- permissions;
- filtros;
- views e viewsets;
- URLs.

Views não devem concentrar consultas complexas nem operações transacionais extensas.

### `services`

Use services para operações de escrita e casos de uso, por exemplo:

- cadastrar paciente e vínculos;
- alterar status clínico;
- finalizar evolução;
- gerar exportação;
- registrar pagamento;
- cancelar ou reagendar sessão.

Services não devem depender de `request`, `Response` ou classes de view do DRF.

### `selectors`

Use selectors para consultas reutilizáveis ou complexas:

- pacientes acessíveis ao usuário;
- prontuários autorizados;
- resumo administrativo;
- indicadores financeiros;
- consultas otimizadas para serializers.

Selectors devem retornar `QuerySet`, entidades ou estruturas explicitamente definidas.

## Direção das dependências

```text
API
 ↓
services / selectors
 ↓
models e regras de domínio
 ↓
integrações e infraestrutura
```

Models e regras de domínio não devem importar views ou serializers.

## Regras obrigatórias de segurança

- `get_queryset()` deve aplicar isolamento de dados;
- permissions por objeto complementam, mas não substituem, o isolamento do queryset;
- IDs enviados pelo frontend não podem determinar clínica ou proprietário sem validação;
- prontuários e documentos clínicos não devem ser registrados integralmente em logs;
- uploads devem validar tamanho, extensão, tipo e autorização de download;
- operações compostas devem usar `transaction.atomic()` quando necessário;
- dados de uma clínica ou terapeuta não podem aparecer para outro contexto por manipulação de URL ou payload.

## Regras de migrations

- não editar migrations já aplicadas;
- não apagar migrations para simplificar histórico;
- não renomear apps existentes sem estratégia de estado e banco;
- executar `makemigrations --check --dry-run` antes de concluir alterações;
- preservar `AppConfig.name` e labels existentes.

## Regras de desempenho

- usar `select_related` para FK e OneToOne;
- usar `prefetch_related` para relacionamentos reversos e M2M;
- evitar queries dentro de loops;
- usar `exists`, `count`, `annotate` e `aggregate` de forma apropriada;
- revisar índices dos campos usados em filtros e ordenações;
- manter paginação em endpoints de coleção.

## Validação obrigatória

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
pytest --cov=apps --cov=core
```

A CI do GitHub executa esses comandos em pull requests direcionadas à `main`.

## Alterações aplicadas nesta etapa

- inclusão da skill `django-expert` em `skills/django-expert/SKILL.md`;
- criação de settings exclusivo para testes;
- configuração do pytest para usar `elo_terapeutico.settings.test`;
- modernização dos settings de produção para Django 5;
- remoção de cópias `*.full` do módulo de usuários;
- remoção do arquivo legado `backend/settings/dev.py`;
- documentação do padrão arquitetural.

## Próxima etapa técnica

A consolidação interna dos apps deve ocorrer em mudanças pequenas e testáveis:

1. mover definições de URLs para `api/urls.py` mantendo shims temporários;
2. extrair permissions das views;
3. extrair operações de escrita para services;
4. extrair consultas reutilizáveis para selectors;
5. atualizar imports e testes por domínio;
6. remover shims apenas após confirmação de que nenhum consumidor depende deles.

Essa ordem reduz risco de quebra de imports, migrations e contratos da API.
