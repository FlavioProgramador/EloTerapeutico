# Mapeamento arquitetural do backend

Branch de trabalho: `codex/refatoracao-arquitetura-backend-final`.

## Estado atual

O backend utiliza Django e Django REST Framework. A API pública permanece em `/api/v1/`.

Apps existentes:

- `users`: conta, autenticação e perfil profissional;
- `patients`: cadastro administrativo, vínculos, lembretes e convites;
- `records`: anamnese, evoluções, documentos, formulários e exportações;
- `agenda`: consultas, recorrências, salas, bloqueios, pacotes e teleatendimento;
- `financeiro`: transações, pagamentos e relatórios;
- `core`: recursos compartilhados entre domínios.

## Problemas encontrados

1. A refatoração anterior criou diretórios `api/`, mas alguns arquivos apenas reexportam módulos antigos.
2. Existem imports curinga e módulos temporários mantidos como permanentes.
3. O domínio clínico mantém arquivos paralelos e variantes `v2`.
4. Agenda usa pastas genéricas `view_parts`, `serializer_parts` e `model_parts`.
5. Regras de escrita e consultas complexas ainda aparecem em views.
6. Há arquivos `.full` deixados por uma refatoração anterior.
7. Ferramentas de qualidade não estão centralizadas em `pyproject.toml`.

## Decisões

- Preservar apps, labels, tabelas, migrations e endpoints públicos.
- Manter o pacote global `elo_terapeutico`; renomeá-lo agora aumentaria o risco sem ganho de domínio.
- Criar `elo_terapeutico/api_urls.py` para centralizar as rotas da API.
- Tornar `api/` a implementação real, sem wrappers permanentes.
- Usar services para escrita e selectors somente para consultas complexas reutilizadas.
- Consolidar o prontuário antes de remover variantes antigas.
- Manter exportações clínicas dentro de `records`, pois pertencem ao ciclo de vida do prontuário.
- Não criar apps vazios apenas para reproduzir uma árvore de referência.

## Estrutura-alvo

```text
backend/
├── elo_terapeutico/
│   ├── api_urls.py
│   ├── urls.py
│   └── settings/
├── core/
├── apps/
│   ├── users/{api,services,selectors,tests}
│   ├── patients/{api,serializers,services,selectors,tests}
│   ├── records/{api,models,serializers,services,selectors,tasks,tests}
│   ├── agenda/{api,models,serializers,services,selectors,tests}
│   └── financeiro/{api,serializers,services,selectors,tests}
└── tests/
```

## Ordem de implementação

1. configuração global, rotas e ferramentas;
2. remoção de artefatos comprovadamente sem uso;
3. API definitiva por recurso;
4. extração de services e selectors;
5. consolidação do prontuário;
6. testes de arquitetura, contratos e desempenho;
7. documentação final e validação de CI.
