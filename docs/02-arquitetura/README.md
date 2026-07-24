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

O Elo Terapêutico usa uma arquitetura web em duas aplicações principais:

- **Next.js** fornece a interface, o BFF e os fluxos públicos controlados;
- **Django REST Framework** concentra regras de negócio, autorização, persistência e integrações.

O PostgreSQL é a fonte de verdade dos domínios transacionais. Redis fornece cache e rate limit em produção, além de broker e result backend do Celery. As tarefas assíncronas são separadas nas filas `default`, `exports`, `uploads` e `communications`, com agendamento periódico pelo Celery Beat.

Arquivos usam filesystem no desenvolvimento e podem usar Azure Blob privado em produção. As integrações externas incluem Asaas, LiveKit, SMTP, WhatsApp Business e SMS, todas condicionadas à configuração e validação operacional.

O domínio `apps.organizations` implementa organização, membership, papéis, convites e configurações. A produção ativa autenticação tenant-aware e o header `X-Organization-ID`; módulos legados ainda precisam de revisão transversal para garantir que todo ownership esteja vinculado à organização correta.

## Princípios

```text
URLs
→ Views
→ Serializers e Permissions
→ Services e Selectors
→ Models
```

```text
Tasks, Signals e Commands
→ Services
→ Integrations e Infrastructure
```

- o frontend não é fronteira de autorização;
- o PostgreSQL mantém estados duráveis e auditáveis;
- o Redis não deve receber conteúdo clínico completo;
- tasks Celery devem ser entradas finas e idempotentes;
- integrações convertem erros externos em exceções controladas;
- ambiente local e produção possuem topologias e responsabilidades diferentes.

[Voltar ao índice](../README.md)
