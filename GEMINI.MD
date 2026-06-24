# AGENTS.md — Elo Terapêutico

## Objetivo

O Elo Terapêutico é uma plataforma de gestão para terapeutas.

Principais módulos:

- Autenticação
- Dashboard
- Pacientes
- Agenda
- Sessões
- Prontuários
- Financeiro
- Relatórios
- Configurações
- Recursos de IA

## Arquitetura

- Frontend: Next.js com TypeScript
- Backend: Django REST Framework
- Banco de dados: PostgreSQL
- Autenticação: JWT
- Infraestrutura: Docker
- Estilização: definir conforme o projeto existente

## Regras obrigatórias

- Nunca armazenar senhas em texto puro.
- Nunca registrar dados sensíveis em logs.
- Nunca adicionar segredos ou tokens ao Git.
- Nunca usar dados reais de pacientes em testes.
- Toda consulta deve respeitar o terapeuta autenticado.
- Um terapeuta nunca pode acessar pacientes de outro terapeuta.
- Validar dados no frontend e no backend.
- Toda funcionalidade nova deve possuir testes.
- Não alterar contratos de API sem documentar a mudança.
- Não instalar dependências sem justificar.

## Frontend

- Evitar aparência genérica de dashboard produzido por IA.
- Utilizar hierarquia visual clara.
- Manter responsividade em celular, tablet e desktop.
- Usar animações apenas quando ajudarem na compreensão.
- Manter estados de loading, erro, vazio e sucesso.
- Garantir navegação por teclado e acessibilidade básica.

## Backend

- Separar regras de negócio de controllers e views.
- Utilizar services quando a lógica crescer.
- Evitar queries N+1.
- Adicionar índices quando necessários.
- Validar permissões por objeto.
- Utilizar transações para operações críticas.

## Processo de conclusão

Antes de considerar uma tarefa concluída:

1. Rodar lint.
2. Rodar testes.
3. Verificar erros de TypeScript.
4. Conferir migrations.
5. Testar o fluxo principal.
6. Resumir arquivos alterados.
7. Informar riscos ou limitações restantes.