# Erros da API

O DRF usa exception handler customizado. O formato pode variar entre validações de serializer e respostas explícitas legadas; clientes devem tratar `detail`, `error` e erros por campo de forma defensiva.

## Códigos comuns

| Código | Significado |
| ---: | --- |
| 200 | leitura/ação concluída |
| 201 | recurso criado |
| 204 | operação sem corpo, quando usada |
| 400 | payload ou transição inválida |
| 401 | autenticação ausente/inválida |
| 403 | autenticado sem permissão ou webhook inválido |
| 404 | recurso inexistente ou fora do escopo |
| 409 | conflito, quando endpoint o utiliza |
| 429 | rate limit |
| 500 | falha interna controlada pelo handler |
| 502 | gateway Asaas indisponível/erro externo |

## Princípios

- não retornar traceback em produção;
- não repassar credenciais ou payload bruto do gateway;
- não revelar se e-mail existe em login/reset;
- mensagens públicas devem orientar sem expor arquitetura;
- logs internos devem usar IDs técnicos e tipo de exceção, não conteúdo clínico.

[Voltar](README.md)
