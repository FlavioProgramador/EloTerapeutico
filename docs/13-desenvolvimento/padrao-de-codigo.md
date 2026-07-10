# Padrão de código

## Python/Django

- formatação e imports pelo Ruff;
- type hints em código novo quando úteis;
- models com constraints e métodos locais;
- serializers para validação HTTP;
- services/actions para operações de domínio;
- selectors para leitura e isolamento;
- views pequenas;
- `transaction.atomic` para operações compostas;
- `select_for_update` quando concorrência exige;
- mensagens públicas sem detalhes internos;
- testes próximos ao app.

## TypeScript/React

- tipos explícitos nas fronteiras;
- server/client components escolhidos conscientemente;
- TanStack Query para estado remoto;
- hooks por feature;
- formulários com Zod/React Hook Form quando aplicável;
- componentes compartilhados sem regra de negócio;
- acessibilidade semântica;
- evitar `any` e efeitos desnecessários;
- não registrar tokens ou payloads clínicos.

## Migrations

- gerar a partir dos models;
- revisar SQL/plan;
- seeds idempotentes;
- operações destrutivas em etapas;
- não editar migration já aplicada sem estratégia;
- testar PostgreSQL para locks/constraints relevantes.

## Documentação

Português do Brasil, links relativos, exemplos fictícios, status explícito e referência ao código.

[Voltar](README.md)
