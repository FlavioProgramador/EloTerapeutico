# 02 — Arquitetura

## Conteúdo

- [Arquitetura geral](arquitetura-geral.md)
- [Backend](backend.md)
- [Frontend](frontend.md)
- [Componentização do frontend](componentizacao-frontend.md)
- [Banco de dados](banco-de-dados.md)
- [Integrações](integracoes.md)
- [Armazenamento de arquivos](armazenamento-de-arquivos.md)
- [Filas e processamento assíncrono](filas-e-processamento-assincrono.md)
- [Estrutura de pastas](estrutura-de-pastas.md)
- [Fluxo de requisição](fluxo-de-requisicao.md)
- [Diagramas](diagramas/contexto.md)

## Resumo

O Elo Terapêutico usa uma arquitetura web em duas aplicações: frontend Next.js e backend Django REST Framework. O PostgreSQL persiste dados transacionais, enquanto arquivos podem usar filesystem ou Azure Blob. Exportações clínicas são processadas por um worker separado que utiliza o próprio banco como fila.

A arquitetura atual organiza propriedade por usuário/terapeuta. Não existe uma camada explícita de tenant/clínica integrada à `main` neste documento.

[Voltar ao índice](../README.md)
