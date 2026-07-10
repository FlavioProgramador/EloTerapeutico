# Retenção e exclusão

## Situação atual

- pacientes possuem arquivamento lógico;
- formulários, templates e documentos possuem estados de arquivamento;
- evoluções bloqueadas são retificadas por aditivo, preservando histórico;
- logs de auditoria são imutáveis pelo model;
- exportações possuem status `EXPIRED`, mas não há prazo global documentado;
- não foi localizada política automática única de retenção ou purge.

## Não definir prazos fictícios

Prazos dependem da finalidade, base legal, contratos, profissão, obrigações regulatórias e litígios. Devem ser aprovados por jurídico/privacidade e então implementados.

## Política a formalizar

Para cada categoria:

1. finalidade;
2. início da retenção;
3. prazo;
4. evento de suspensão legal;
5. arquivamento;
6. anonimização ou exclusão;
7. tratamento de backups;
8. evidência da execução;
9. responsável e aprovador.

## Exclusão técnica

- verificar relações `PROTECT` e cascatas;
- impedir exclusão parcial que destrua integridade clínica;
- anonimizar quando permitido e adequado;
- remover arquivos e links, não apenas linha do banco;
- considerar cópias, caches e backups;
- registrar ação sem guardar dados eliminados;
- testar em ambiente não produtivo.

## Backups

Dados excluídos podem permanecer em backups até expiração segura. O processo deve impedir restauração permanente de dados já eliminados sem reaplicar a lista de exclusões.

[Voltar](README.md)
