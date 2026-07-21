# Migração multi-tenant

## Estratégia

A implantação utiliza quatro fases:

```text
expand -> backfill -> validate -> contract
```

Não reescrever migrations históricas e não tornar uma FK obrigatória antes de associar os registros existentes.

## 1. Expand

- aplicar a migration inicial de `organizations`;
- adicionar `organization` temporariamente nullable aos apps migrados;
- manter os IDs e relacionamentos existentes;
- não duplicar registros clínicos, consultas ou transações.

## 2. Backfill

Executar primeiro em modo de simulação:

```bash
python manage.py backfill_organizations \
  --dry-run \
  --batch-size 500 \
  --report-file reports/backfill-dry-run.json
```

Depois executar a associação real:

```bash
python manage.py backfill_organizations \
  --batch-size 500 \
  --resume \
  --report-file reports/backfill.json
```

Para cada profissional legado, o comando cria ou reutiliza:

- organização individual;
- membership `owner` ativa;
- configurações da organização;
- perfil profissional.

Os recursos são associados por relações determinísticas, principalmente paciente e profissional responsável.

## 3. Validate

```bash
python manage.py audit_tenant_integrity \
  --format=json \
  --report-file reports/tenant-audit.json \
  --fail-on-error
```

A validação bloqueia a implantação quando encontra:

- recurso sem organização;
- relação entre tenants diferentes;
- organização sem proprietário ativo;
- mais de uma membership padrão por usuário;
- vínculo profissional inválido.

## 4. Contract

Depois do relatório sem erros:

- tornar `organization` obrigatório;
- adicionar constraints e índices finais;
- remover fallbacks baseados apenas em terapeuta;
- ativar `TENANT_ENFORCEMENT_ENABLED`;
- executar testes de isolamento e build.

## Produção

Em produção o enforcement é obrigatório. O deploy deve falhar quando a configuração multi-tenant não estiver ativa.

Ordem operacional recomendada:

1. backup validado do PostgreSQL e storage;
2. maintenance window;
3. migrations expand;
4. backfill;
5. auditoria;
6. migrations contract;
7. workers e aplicação;
8. smoke tests com duas organizações;
9. liberação do tráfego.

## Rollback

Enquanto apenas a fase expand estiver aplicada, o código anterior pode ignorar as FKs novas.

Após contract, rollback exige:

- restaurar aplicação compatível;
- preservar as colunas `organization_id`;
- não remover organizações ou memberships criadas;
- nunca desfazer o backfill apagando dados.
