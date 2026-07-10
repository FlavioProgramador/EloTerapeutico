# Health checks

## Endpoint existente

`GET /api/health/` consulta o banco e retorna:

- `200` com `{"status":"ok","database":"ok"}`;
- `503` com `status=degraded` e banco indisponível.

O Docker Compose usa esse endpoint no health check do backend.

## Limitações

O endpoint não valida:

- Redis;
- Azure Blob;
- Asaas;
- SMTP;
- worker;
- espaço em disco;
- migrations pendentes.

Não adicione dependências externas lentas ao liveness. Separe:

- **liveness:** processo responde;
- **readiness:** banco/cache/storage essenciais;
- **startup:** migrations e inicialização;
- **synthetic:** fluxo completo fora do endpoint de health.

## Worker

Não há health endpoint próprio comprovado. Use heartbeat/métrica, idade de jobs e logs do processo. Reiniciar worker não deve duplicar job graças à reserva e idempotência do estado, mas testes de falha são necessários.

[Voltar](README.md)
