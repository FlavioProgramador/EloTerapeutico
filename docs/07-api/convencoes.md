# Convenções da API

## Formato

- JSON UTF-8 para requisições comuns;
- `multipart/form-data` para uploads;
- datas em ISO 8601;
- valores monetários tratados como decimal/string na fronteira quando necessário;
- IDs internos inteiros e alguns IDs públicos UUID.

## Paginação

A paginação global usa 20 itens por página. Listagens podem aceitar `page`, filtros Django, busca e ordenação conforme ViewSet/FilterSet.

Exemplo:

```text
GET /api/v1/patients/?page=2&search=Ana&ordering=full_name
```

## Versionamento

O prefixo `/api/v1/` é o mecanismo atual. Não foi localizada uma política completa de depreciação. Mudanças incompatíveis exigem nova versão ou período de compatibilidade.

## Idempotência

Documentos gerados aceitam chave de idempotência no modelo. Webhooks usam ID/hash. Outros POSTs não devem ser presumidos idempotentes sem contrato explícito.

## Dados de exemplo

Use apenas valores fictícios. Nunca copie tokens, chaves, CPF, dados clínicos ou URLs privadas reais para tickets ou documentação.

[Voltar](README.md)
