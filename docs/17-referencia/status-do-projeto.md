# Status do projeto

## Revisão documentada

- commit-base: `176cba63ed3edf1cee232363e5a89c4b7fda28ac`;
- data da análise: 10/07/2026;
- branch documental: `docs/refatoracao-completa`;
- estado: desenvolvimento ativo;
- deploy em produção: não comprovado pelo repositório.

## Síntese

O projeto possui backend e frontend funcionais, migrations, testes, Docker Compose, worker de exportação, workflows de qualidade e integração Asaas. A amplitude funcional é maior que a documentação anterior indicava.

A principal restrição arquitetural é a ausência de tenant/clínica explícito. Há isolamento por terapeuta em diversos domínios, mas isso não deve ser apresentado como multi-tenancy completo.

## Critério de atualização

Este arquivo deve ser revisto quando houver mudança relevante em arquitetura, módulos, segurança, ambiente de produção ou modelo de propriedade dos dados.

[Voltar](README.md)
