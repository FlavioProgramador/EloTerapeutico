# 12 — Operação

- [Docker e workers](docker-e-workers.md)
- [Logs e monitoramento](logs.md)
- [Health checks](health-checks.md)
- [Backup e restauração](backup-e-restauracao.md)
- [Resposta a falhas](resposta-a-falhas.md)
- [Telemedicina](telemedicina.md)

## Escopo

Os runbooks cobrem desenvolvimento, suporte e preparação de produção. A existência de health checks e logs no código não comprova disponibilidade, backup, observabilidade ou recuperação no ambiente implantado.

Prioridades operacionais:

1. preservar confidencialidade e isolamento por organização;
2. evitar alterações destrutivas sem backup;
3. manter PostgreSQL como fonte dos estados duráveis;
4. manter apenas uma instância de Celery Beat sem coordenação adicional;
5. monitorar workers, filas, retries e jobs presos;
6. validar integrações externas em staging;
7. registrar incidentes sem copiar dados clínicos ou segredos.

[Voltar ao índice](../README.md)
