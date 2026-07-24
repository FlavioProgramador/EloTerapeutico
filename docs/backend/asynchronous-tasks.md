# Workers e processamento assíncrono

> Esta página permanece para compatibilidade com links antigos. A documentação canônica está em [Filas e processamento assíncrono](../02-arquitetura/filas-e-processamento-assincrono.md), [Matriz de containers](../17-referencia/matriz-de-containers.md) e [Docker e workers](../12-operacao/docker-e-workers.md).

## Arquitetura atual

O backend usa PostgreSQL para estados duráveis, Redis como broker/result backend e Celery para execução assíncrona.

Filas atuais:

| Fila | Serviço |
| --- | --- |
| `default` | `celery-worker-default` |
| `exports` | `celery-worker-exports` |
| `uploads` | `celery-worker-uploads` |
| `communications` | `celery-worker-communications` |

Tarefas periódicas são publicadas pelo serviço `celery-beat`.

Os antigos processos baseados apenas em management commands e serviços chamados `worker`, `communications-worker` ou `communications-scheduler` representam fases anteriores da arquitetura e não correspondem ao Compose atual.

## Princípios preservados

- PostgreSQL mantém estado, auditoria e idempotência;
- tasks recebem identificadores mínimos;
- conteúdo clínico e credenciais não vão para Redis ou logs;
- workers reservam jobs de forma concorrente e recuperável;
- integração externa ocorre fora de transação longa;
- retries possuem limite e classificação de erro;
- Celery Beat agenda, mas não executa o trabalho final;
- apenas uma instância de Beat deve ficar ativa sem coordenação adicional.

## Execução sem Docker

```bash
cd backend
celery -A config worker --loglevel=INFO --queues=default --concurrency=1
celery -A config worker --loglevel=INFO --queues=exports --concurrency=1
celery -A config worker --loglevel=INFO --queues=uploads --concurrency=1
celery -A config worker --loglevel=INFO --queues=communications --concurrency=2
celery -A config beat --loglevel=INFO
```

Consulte a página canônica para roteamento de tasks, schedule completo, variáveis, observabilidade e operação.
