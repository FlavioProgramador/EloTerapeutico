# Workers e processamento assíncrono

## Arquitetura atual

O backend utiliza filas persistidas no banco de dados e management commands executados como workers. A configuração atual não depende de Celery ou Redis para os fluxos documentados.

Serviços definidos no Docker Compose:

| Serviço | Comando | Responsabilidade |
| --- | --- | --- |
| `worker` | `python manage.py run_export_worker` | Processar exportações clínicas persistidas |
| `communications-worker` | `python manage.py process_communications --sleep 5` | Processar envios pendentes |
| `communications-scheduler` | comandos em ciclo a cada 300 segundos | Agendar automações, retentar falhas e limpar tokens expirados |

## Vantagens da fila persistida

- estado observável no banco;
- reprocessamento controlado;
- histórico de tentativas;
- recuperação após reinício do processo;
- concorrência coordenada por transação;
- ausência de dependência obrigatória de broker no ambiente local.

## Estados de job

Fluxo genérico usado por exportações e aplicável a tarefas persistidas:

```text
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED
PENDING/COMPLETED → EXPIRED
```

O significado de cada estado deve ser confirmado no model específico.

- `PENDING`: persistido e aguardando worker;
- `PROCESSING`: reservado por um worker;
- `COMPLETED`: resultado persistido com sucesso;
- `FAILED`: tentativa finalizada com erro sanitizado;
- `EXPIRED`: resultado ou token não está mais disponível.

## Reserva concorrente

Workers concorrentes devem impedir que o mesmo item seja processado simultaneamente. O padrão recomendado é:

```python
with transaction.atomic():
    job = (
        ExportJob.objects
        .select_for_update(skip_locked=True)
        .filter(status=ExportJob.Status.PENDING)
        .order_by("created_at")
        .first()
    )
```

A implementação real pode variar, mas deve preservar reserva exclusiva, transição atômica e recuperação de itens abandonados.

## Idempotência

Uma tarefa é idempotente quando repetir a mesma execução não cria resultados duplicados nem aplica a mesma mudança de estado duas vezes.

Cada worker deve documentar:

- chave natural ou técnica de idempotência;
- comportamento ao encontrar resultado já criado;
- ações que podem ser repetidas;
- ações que exigem compensação;
- efeito de reinício após falha parcial.

## Exportações clínicas

O worker de exportação deve:

1. reservar job pendente;
2. marcar início do processamento;
3. carregar dados no escopo do solicitante;
4. montar o documento ou arquivo;
5. persistir em storage privado;
6. atualizar hash, caminho e expiração quando aplicável;
7. marcar `COMPLETED`;
8. em falha, registrar mensagem sanitizada e marcar `FAILED`;
9. nunca incluir conteúdo clínico integral em logs.

## Comunicações

### Processamento de fila

`process_communications` seleciona comunicações aptas, cria ou atualiza tentativas e delega ao provider do canal.

Configurações:

- `COMMUNICATIONS_BATCH_SIZE`;
- `COMMUNICATIONS_MAX_ATTEMPTS`;
- `COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES`;
- `COMMUNICATIONS_DEFAULT_TIMEZONE`;
- `COMMUNICATIONS_REPLY_TO`.

### Agendamento de automações

`schedule_communication_automations` materializa comunicações a partir de regras ativas. Deve evitar duplicação ao executar novamente no mesmo período.

### Retentativas

`retry_failed_communications` deve retentar somente falhas elegíveis. Erros permanentes, como destinatário inválido ou canal não configurado, não devem entrar em loop infinito.

### Limpeza de tokens

`cleanup_expired_communication_tokens` remove ou invalida tokens públicos expirados sem apagar o histórico necessário da comunicação.

## Política de retry

Documente por tarefa:

- máximo de tentativas;
- intervalo ou backoff;
- erros transitórios;
- erros permanentes;
- timeout;
- condição para intervenção manual.

Exemplo de classificação:

| Falha | Retry automático |
| --- | --- |
| timeout de provider | Sim, com limite |
| conexão temporariamente indisponível | Sim, com limite |
| credencial inválida | Não; exige configuração |
| payload rejeitado por validação | Não |
| destinatário inválido | Não |
| evento já processado | Não; tratar como idempotente |

## Recuperação de jobs abandonados

Um processo pode morrer após marcar um item como `PROCESSING`. A rotina de recuperação deve identificar itens acima do timeout configurado e:

- devolver para `PENDING` quando seguro;
- marcar `FAILED` quando a repetição não for segura;
- incrementar tentativa;
- registrar motivo técnico sanitizado.

## Logs e observabilidade

Campos úteis:

- identificador do job;
- tipo de tarefa;
- status anterior e novo;
- número da tentativa;
- duração;
- provider;
- código de erro interno;
- identificador de correlação.

Nunca registrar:

- token público em texto puro;
- credenciais;
- corpo clínico;
- e-mail, telefone ou documento sem mascaramento;
- payload completo de pagamento.

## Operação sem Docker

Execute em terminais separados:

```bash
cd backend
python manage.py run_export_worker
python manage.py process_communications --sleep 5
python manage.py schedule_communication_automations
python manage.py retry_failed_communications
python manage.py cleanup_expired_communication_tokens
```

Os comandos de scheduler executados uma única vez não substituem um agendador contínuo. No Docker Compose, o serviço executa o ciclo a cada cinco minutos.

## Testes mínimos

- reserva concorrente sem processamento duplicado;
- recuperação de job abandonado;
- idempotência após reinício;
- transições válidas e inválidas;
- limite de tentativas;
- falha transitória e permanente;
- storage indisponível;
- provider indisponível;
- isolamento pelo solicitante;
- limpeza de token expirado;
- logs sem dados sensíveis.
