# Divisão de responsabilidade e conflitos

| Agente | Responsabilidade principal | Evitar alterar |
|---|---|---|
| `landing_page` | Páginas públicas, design system e UI visual | Backend de domínio, autenticação e banco |
| `agenda` | Calendário, consultas, disponibilidade e conflitos | Financeiro e conteúdo de prontuário |
| `pacientes_prontuarios` | Pacientes, sessões e prontuários | Financeiro, landing page e estratégia de autenticação |
| `financeiro` | Receitas, despesas, cobranças e relatórios | Prontuários e regras clínicas |
| `autenticacao_permissoes` | Identidade, sessão/JWT e autorização | Redesign visual e regras financeiras |
| `testes_qa` | Testes e evidência de regressão | Redesign de features e grandes refactors |
| `seguranca` | Auditoria somente leitura | Qualquer edição |
| `documentacao_docker` | Docs e infraestrutura local | Lógica de negócio |

## Arquivos compartilhados de alto risco

Os seguintes tipos de arquivo podem gerar conflitos entre agentes:

- modelos centrais de usuário/terapeuta;
- configuração global de rotas;
- schemas ou tipos compartilhados;
- arquivo principal de configuração do backend;
- layout raiz e componentes globais;
- migrations;
- Docker Compose;
- lockfiles.

Quando um agente precisar alterar um arquivo compartilhado:

1. Faça a menor mudança possível.
2. Registre o motivo no relatório.
3. Não reformate o arquivo inteiro.
4. Não sobrescreva trabalho existente.
5. Rebase ou atualize a branch antes de abrir o PR.
6. Solicite revisão do agente proprietário do contrato afetado.
