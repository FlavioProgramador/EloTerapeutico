# Problemas comuns

## Backend não inicia

**Sintoma:** import error, ImproperlyConfigured ou conexão recusada.

**Diagnóstico:** confirme ambiente virtual, `DJANGO_SETTINGS_MODULE`, `.env`, banco e dependências nativas.

**Solução:** instale `requirements/dev.txt`, use settings dev localmente, configure placeholders locais e rode `python manage.py check`.

**Prevenção:** CI, `.env.example` atualizado e Docker.

## Segredo rejeitado em produção

**Causa:** ausente, curto, placeholder ou igual a outro segredo.

**Solução:** gere valores distintos no secret manager; não publique valores no ticket.

## Migrations pendentes

```bash
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate --plan
```

Revise antes de aplicar. Não crie migration automática no servidor.

## Frontend não encontra API

Valide `NEXT_PUBLIC_API_URL` **antes do build**, barra final, TLS, CORS e DNS. Refaça o build após mudar variável pública.

## Erro CORS

Desenvolvimento usa CORS aberto; produção exige origem exata com esquema. Não use wildcard com credenciais.

## Refresh inválido

Pode estar expirado, em blacklist, pertencer a outro usuário ou ter sido invalidado por troca de senha. Limpe sessão e autentique novamente; não desative validação.

## Docker não conecta ao banco

Dentro dos containers, use host `db`, não `localhost`. Confirme `POSTGRES_PASSWORD`, `DATABASE_URL`, health e volume.

## Worker não processa

Confirme processo `run_export_worker`, banco compartilhado, jobs PENDING e data `next_attempt_at`. Verifique WeasyPrint e storage.

## Upload rejeitado

Confira até 10 MB, extensão permitida, MIME correto e arquivo real não corrompido. Renomear extensão não corrige magic bytes.

## Azure não configurado

Sem connection string, production settings usa filesystem salvo se `PRIVATE_MEDIA_STORAGE_REQUIRED=True`. Para produção clínica, habilite a flag e configure container privado.

## Asaas não configurado/502

Confirme API key no backend, base URL e rede. Produção não aceita sandbox. Erro 502 é resposta controlada; consulte logs por operação, sem credencial.

## Webhook rejeitado

Sincronize token em Asaas e aplicação. Headers aceitos incluem `asaas-access-token`. Teste deduplicação e não remova autenticação.

## Build frontend falha

```bash
rm -rf node_modules .next
npm ci
npm run lint
npm run typecheck
npm run build
```

No Windows, remova diretórios pelo PowerShell/Explorer se necessário.

## GitGuardian/secret scanning sinaliza exemplo

Use placeholders textuais como `configure-no-secret-manager`; não gere strings de alta entropia na documentação. Se um segredo real foi commitado, revogue-o antes de limpar histórico.

## Dependência vulnerável

Reproduza com `pip-audit` ou auditoria npm, confirme alcance, atualize dentro das faixas compatíveis, rode testes e documente risco quando não houver correção imediata.

[Voltar](README.md)
