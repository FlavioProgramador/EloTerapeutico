# Elo Terapêutico

## Visão geral

O Elo Terapêutico é uma plataforma SaaS de gestão clínica voltada para psicólogos, terapeutas e clínicas.

O sistema centraliza pacientes, agenda, prontuários, documentos clínicos, planos terapêuticos, controle financeiro, relatórios e configurações da clínica.

O produto deve transmitir confiança, organização, segurança, acolhimento e profissionalismo.

## Objetivo

Oferecer uma plataforma completa para que profissionais da área terapêutica possam administrar sua rotina clínica com segurança, produtividade e boa experiência de uso.

## Público-alvo

- Psicólogos;
- terapeutas;
- profissionais autônomos;
- pequenas clínicas;
- secretários e colaboradores autorizados.

## Tecnologias

### Frontend

- Next.js;
- React;
- TypeScript;
- Tailwind CSS;
- TanStack Query;
- React Hook Form;
- Zod;
- componentes reutilizáveis;
- suporte a tema claro e escuro.

### Backend

- Python;
- Django;
- Django REST Framework;
- PostgreSQL;
- autenticação JWT;
- arquitetura modular;
- testes com Pytest.

### Infraestrutura

- Docker;
- GitHub Actions;
- possibilidade de implantação no Microsoft Azure;
- armazenamento de arquivos clínicos em serviço externo seguro.

## Principais módulos

- Autenticação e gerenciamento de usuários;
- dashboard;
- pacientes;
- agenda e consultas;
- prontuário clínico;
- anamnese;
- plano terapêutico;
- documentos;
- financeiro;
- relatórios;
- configurações da clínica;
- auditoria e histórico de operações.

## Regras importantes

1. Dados clínicos são sensíveis e devem ser tratados com alto nível de segurança.
2. Um terapeuta ou clínica nunca pode acessar dados pertencentes a outro tenant.
3. Toda consulta, atualização, exclusão, importação e exportação deve validar autorização.
4. Nunca registrar prontuários, CPF, senhas, tokens ou informações clínicas completas em logs.
5. Nunca utilizar dados reais de pacientes em testes.
6. Nunca adicionar senhas, tokens, chaves de API ou arquivos `.env` ao Git.
7. Preservar compatibilidade com tema claro e escuro.
8. Preservar responsividade para desktop, tablet e celular.
9. Reutilizar o design system e os componentes existentes.
10. Não duplicar componentes ou regras já presentes no projeto.
11. Não adicionar dependências sem necessidade comprovada.
12. Não alterar autenticação, autorização, criptografia ou arquitetura multi-tenant sem solicitação explícita.
13. Não criar migrations desnecessárias.
14. Não alterar contratos da API sem atualizar frontend, testes e documentação.
15. Mudanças devem ser pequenas, organizadas e fáceis de revisar.

## Padrões de desenvolvimento

Antes de alterar qualquer código:

1. Ler `README.md`.
2. Ler `AGENTS.md`, caso exista.
3. Ler a documentação dentro de `docs/`.
4. Inspecionar a arquitetura atual.
5. Identificar os padrões já utilizados.
6. Verificar se já existe implementação semelhante.
7. Planejar a alteração antes de editar arquivos.

Os commits devem:

- estar em português;
- seguir Conventional Commits;
- possuir uma responsabilidade clara;
- não misturar alterações independentes;
- não incluir arquivos temporários ou segredos.

Exemplos:

- `feat: adiciona filtro de pacientes`
- `fix: corrige isolamento de prontuários`
- `refactor: reorganiza componentes da agenda`
- `test: adiciona cobertura para permissões`
- `docs: atualiza documentação do módulo financeiro`

## Validação do frontend

Quando alterar o frontend, executar:

```bash
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

O projeto utiliza npm. Não utilizar pnpm ou yarn sem solicitação explícita.

## Validação do backend

Quando alterar o backend, executar:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

Quando necessário, executar também:

```bash
python manage.py migrate
```

## Diretrizes de interface

A interface deve:

* parecer um produto profissional e real;
* evitar aparência genérica de template;
* utilizar boa hierarquia visual;
* ter espaçamentos consistentes;
* apresentar feedback de carregamento, sucesso e erro;
* possuir estados vazios úteis;
* ser acessível por teclado;
* utilizar HTML semântico;
* possuir nomes acessíveis em botões apenas com ícones;
* manter contraste adequado;
* evitar excesso de informações na mesma tela.

## Diretrizes para o agente

O agente deve:

* investigar antes de alterar;
* explicar brevemente o plano;
* fazer somente mudanças relacionadas à solicitação atual;
* preservar funcionalidades existentes;
* adicionar ou atualizar testes quando necessário;
* executar validações antes de concluir;
* informar comandos que falharam;
* não afirmar que algo foi testado quando não foi;
* não realizar merge automático;
* não modificar arquivos fora do escopo;
* interromper quando uma decisão de produto ou arquitetura não puder ser inferida com segurança.

## Estado atual

O projeto está em desenvolvimento ativo.

As prioridades gerais são:

* consolidar os módulos clínicos;
* aprimorar segurança e isolamento de dados;
* manter frontend e backend alinhados;
* melhorar testes;
* melhorar acessibilidade;
* preparar a infraestrutura para implantação;
* manter a documentação atualizada.
