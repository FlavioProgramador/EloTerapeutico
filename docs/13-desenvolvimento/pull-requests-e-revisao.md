# Pull Requests e revisão

## Descrição mínima

- problema e contexto;
- solução e limites;
- módulos/rotas/models alterados;
- migrations;
- riscos de autorização, dados e compatibilidade;
- testes executados com comandos;
- screenshots quando a interface muda;
- rollback;
- documentação atualizada.

## Revisão backend

- queryset filtra por proprietário;
- object permission existe;
- serializer não aceita owner/role arbitrário;
- transações e locks são adequados;
- constraints preservam integridade;
- erros não vazam dados;
- logs e auditoria são mínimos;
- downloads/exports revalidam acesso;
- migrations são seguras.

## Revisão frontend

- estados loading/error/empty/success;
- validação acessível;
- dados não são inventados;
- autorização não depende da interface;
- tokens/segredos não aparecem em console;
- URL e caching estão corretos;
- responsividade e teclado;
- lint, typecheck e build.

## Revisão segurança

- ameaça e abuso considerados;
- testes negativos/IDOR;
- uploads e URLs externas;
- redaction;
- dependências;
- segredo/configuração;
- LGPD e minimização.

## Aprovação

Não aprove apenas porque os testes passaram. Verifique a regra, dados, contrato e operação.

[Voltar](README.md)
