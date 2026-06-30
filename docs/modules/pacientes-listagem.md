# Listagem de pacientes

A tela inicial do módulo de Pacientes foi reorganizada para aumentar a densidade de informação e manter a identidade visual do Elo Terapêutico.

## Interface

A página contém:

- cabeçalho com ação de novo cadastro;
- indicadores de total, pacientes ativos e aniversariantes do mês;
- pesquisa com debounce por nome, CPF, telefone ou e-mail;
- filtro rápido de aniversariantes;
- filtros avançados preservados na URL;
- tabela administrativa em desktop e cards em celulares;
- paginação baseada em `pagination.count`, `current_page`, `total_pages`, `next` e `previous`;
- estados de carregamento, erro e listagem vazia;
- exportação CSV usando os filtros aplicados.

## Segurança

A API mantém o isolamento existente:

- terapeutas acessam somente seus pacientes;
- secretárias possuem acesso administrativo de leitura, sem alteração de lembretes;
- administradores preservam as permissões atuais;
- CPF permanece mascarado na listagem;
- atualização de lembretes valida a autorização no backend e gera auditoria;
- acesso ao prontuário continua condicionado ao perfil permitido.

## Backend

A listagem utiliza `PatientReferenceListSerializer`, que acrescenta somente os campos administrativos `birth_date` e `reminders_enabled` ao contrato resumido.

O endpoint abaixo altera o lembrete de forma isolada e auditada:

```text
PATCH /api/v1/patients/{id}/reminders/
{
  "enabled": true
}
```

Pacientes arquivados podem ser consultados com `status=archived` e restaurados pela ação já existente.

## Validação

```bash
docker compose exec frontend npm run lint
docker compose exec frontend npx tsc --noEmit
docker compose exec frontend npm run build

docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend pytest apps/patients -q
```
