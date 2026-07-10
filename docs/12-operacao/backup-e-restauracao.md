# Backup e restauração

**Status: requer implementação operacional.** O repositório não configura backups automáticos.

## Escopo

- PostgreSQL;
- Azure Blob/arquivos;
- configuração não secreta;
- segredos/versionamento no secret manager;
- metadados de deploy;
- logs conforme retenção.

## Requisitos

- criptografia;
- acesso separado de produção;
- cópia imutável/offline conforme risco;
- retenção aprovada;
- monitoramento de sucesso;
- teste periódico de restauração;
- coerência entre banco e arquivos;
- RPO/RTO definidos.

## Procedimento de restauração

1. declarar incidente/janela;
2. selecionar restore point;
3. criar ambiente isolado;
4. restaurar banco;
5. restaurar ou apontar storage compatível;
6. configurar a mesma versão de chaves necessária para descriptografia;
7. executar checks e migrations somente se previsto;
8. validar contagens, integridade e amostras fictícias/controladas;
9. validar auth, exports e downloads;
10. reaplicar exclusões ocorridas após o backup quando aplicável;
11. liberar tráfego com monitoramento;
12. documentar resultado.

## Teste

Backup não testado não é garantia. Registre data, volume, duração, RPO/RTO observado, falhas e responsáveis.

[Voltar](README.md)
