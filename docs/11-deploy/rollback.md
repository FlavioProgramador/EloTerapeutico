# Rollback

## Código

- manter imagem/artefato anterior identificado por SHA;
- reverter tráfego para versão anterior;
- não reconstruir imagem antiga com dependências novas;
- validar compatibilidade do frontend com a API revertida.

## Banco

Migrations Django não são automaticamente seguras para reversão. Antes do deploy:

- revisar `migrate --plan`;
- classificar migration como aditiva, transformacional ou destrutiva;
- preferir expand/contract;
- criar backup;
- testar `migrate <app> <migration_anterior>` quando reversível;
- criar plano manual para dados transformados.

Nunca reverta código para uma versão incompatível com o schema atual.

## Storage

PDFs e uploads criados durante a versão nova podem não ser reconhecidos pela anterior. Preserve arquivos e metadados até investigação; não apague em rollback automático.

## Critérios de acionamento

- aumento de 5xx;
- falha de login/refresh;
- migrations incorretas;
- vazamento ou falha de autorização;
- perda de arquivos;
- worker corrompendo jobs;
- webhook alterando estados indevidamente.

## Registro

Documentar versão, horário, causa, ações, dados afetados, validação e decisão de seguir/reverter.

[Voltar](README.md)
