# Runbook de backfill de organizações

## Preparação

Antes de executar:

- validar backup do banco e storage;
- pausar novas escritas ou abrir janela de manutenção;
- confirmar migrations `organizations` aplicadas;
- criar diretório privado para relatórios;
- garantir espaço e timeout suficientes no banco.

## Simulação

```bash
python manage.py backfill_organizations \
  --dry-run \
  --batch-size 500 \
  --report-file reports/backfill-dry-run.json
```

Revisar:

- profissionais encontrados;
- organizações criadas ou reutilizadas;
- memberships criadas;
- registros associados;
- registros ambíguos;
- falhas por lote.

## Execução

```bash
python manage.py backfill_organizations \
  --batch-size 500 \
  --resume \
  --report-file reports/backfill.json
```

O comando é idempotente. Reexecuções não devem duplicar organizações, memberships, pacientes, consultas, prontuários ou cobranças.

## Escopo reduzido

Por usuário:

```bash
python manage.py backfill_organizations --user-id 42 --report-file reports/user-42.json
```

Por organização já criada:

```bash
python manage.py backfill_organizations \
  --organization-id 00000000-0000-0000-0000-000000000000 \
  --report-file reports/organization.json
```

## Validação

```bash
python manage.py audit_tenant_integrity \
  --format=json \
  --report-file reports/tenant-audit.json \
  --fail-on-error
```

Não aplicar migrations contract quando o comando retornar erros.

## Reparos determinísticos

```bash
python manage.py repair_tenant_integrity --dry-run
python manage.py repair_tenant_integrity
```

O reparo não escolhe arbitrariamente um tenant. Casos ambíguos permanecem pendentes para correção manual.

## Segurança dos relatórios

Relatórios devem conter apenas:

- IDs técnicos;
- nomes de models;
- contagens;
- códigos de erro.

Não registrar conteúdo clínico, CPF, e-mail completo, token, documento, texto de comunicação ou arquivo.

## Critérios de encerramento

- zero recurso tenant-owned sem organização;
- zero relação cruzada;
- toda organização não arquivada com owner ativo;
- no máximo uma membership padrão por usuário;
- smoke test de acesso entre tenant A e tenant B aprovado;
- workers reiniciados com versão tenant-aware.
