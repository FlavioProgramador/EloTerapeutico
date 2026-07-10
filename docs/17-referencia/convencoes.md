# Convenções da documentação

## Situações

- `Status: implementado` — comportamento verificável no código;
- `Status: parcialmente implementado` — há código, mas faltam partes ou configuração;
- `Status: planejado ou não implementado` — não foi localizada implementação suficiente;
- `Requer configuração operacional` — depende do ambiente, segredo ou serviço externo.

## Exemplos

- usam domínios `example.test` e identificadores fictícios;
- nunca incluem tokens, CPFs, dados clínicos ou credenciais reais;
- valores de segredo usam placeholders legíveis, não strings de alta entropia.

## Referências ao código

Caminhos são relativos à raiz do repositório e apresentados entre crases. A documentação evita números de linha para não se tornar obsoleta após pequenas alterações.

## API

- prefixo principal: `/api/v1/`;
- autenticação: `Authorization: Bearer <access-token>`;
- conteúdo padrão: `application/json`;
- uploads usam `multipart/form-data`;
- paginação padrão: 20 itens, salvo customização do endpoint.

[Voltar](README.md)
