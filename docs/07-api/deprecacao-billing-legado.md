# Depreciação do prefixo legado de Billing

## Rota canônica

Todas as integrações novas devem usar:

```text
/api/v1/billing/
```

O prefixo abaixo existe apenas para compatibilidade temporária:

```text
/api/billing/
```

## Comportamento da rota antiga

Enquanto habilitada, a rota antiga executa os mesmos callbacks da API canônica, mas responde com:

```http
Deprecation: true
Sunset: Sun, 31 Jan 2027 23:59:59 GMT
Link: </api/v1/billing/>; rel="successor-version"
Warning: 299 - "Deprecated API: use /api/v1/billing/"
```

Os nomes usados por `reverse()` possuem prefixo `legacy-`. Os nomes públicos originais resolvem sempre para `/api/v1/billing/`.

A árvore legada não é publicada como uma segunda API no OpenAPI.

## Configuração

```text
BILLING_LEGACY_ROUTE_ENABLED=true
BILLING_LEGACY_ROUTE_SUNSET=Sun, 31 Jan 2027 23:59:59 GMT
```

- `BILLING_LEGACY_ROUTE_ENABLED=false` remove o registro da rota durante a inicialização do Django;
- valores inválidos não desligam a compatibilidade por acidente;
- a data de sunset pode ser ajustada por ambiente durante a transição.

## Migração dos consumidores

1. atualizar frontend, workers, scripts e integrações para `/api/v1/billing/`;
2. atualizar o webhook Asaas para `/api/v1/billing/webhooks/asaas/`;
3. observar acessos ao prefixo antigo no proxy/reverse proxy;
4. avisar consumidores externos antes do sunset;
5. definir `BILLING_LEGACY_ROUTE_ENABLED=false` em homologação;
6. validar checkout, webhook, reconciliação e regularização;
7. repetir em produção somente após ausência comprovada de consumidores.

## Rollback

Durante a janela de transição, reativar a variável e reiniciar a aplicação restaura o prefixo antigo sem migration e sem alteração de dados.

A remoção definitiva deve ocorrer em PR próprio depois do sunset e da comprovação de que não existem consumidores.

[Voltar aos endpoints de Billing](endpoints/billing.md)
