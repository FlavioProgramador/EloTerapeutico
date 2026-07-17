# Notificações

## Visão geral

A central de notificações amplia o modelo `InAppNotification` já existente e reutiliza a infraestrutura de comunicações e Celery do projeto.

Suporta:

- notificações no sistema;
- entrega por e-mail;
- preferências por usuário e categoria;
- prioridades;
- leitura e retorno para não lida;
- arquivamento individual e em massa;
- filtros, pesquisa e paginação;
- links internos controlados;
- deduplicação;
- expiração e limpeza;
- preparação explícita para WhatsApp e push, sem fingir integração ativa.

## Modelos

### InAppNotification

Possui UUID público, destinatário, ator opcional, categoria, evento, título, mensagem resumida, prioridade, URL interna, rótulo de ação, metadados sanitizados, leitura, arquivamento e expiração.

### NotificationPreference

Preferência `OneToOne` do usuário, contendo canais, horário de silêncio, fuso, resumo diário e substituições por categoria.

### NotificationDelivery

Registra canal, status, tentativas, provedor, agendamento, envio, falha e próxima tentativa. A falha do e-mail não remove a notificação in-app.

Templates de e-mail reutilizam a infraestrutura de comunicações já existente; não foi criado um segundo mecanismo concorrente de templates.

## API

| Método | Endpoint |
| --- | --- |
| GET | `/api/v1/communications/notifications/` |
| GET | `/api/v1/communications/notifications/{public_id}/` |
| POST | `/api/v1/communications/notifications/{public_id}/read/` |
| POST | `/api/v1/communications/notifications/{public_id}/unread/` |
| POST | `/api/v1/communications/notifications/{public_id}/archive/` |
| POST | `/api/v1/communications/notifications/read-all/` |
| POST | `/api/v1/communications/notifications/archive-read/` |
| GET | `/api/v1/communications/notifications/unread-count/` |
| GET | `/api/v1/communications/notifications/categories/` |
| GET/PATCH | `/api/v1/communications/notifications/preferences/` |

Filtros: `is_read`, `archived`, `category`, `priority`, `search`, `start_date`, `end_date`, `ordering` e paginação DRF.

## Isolamento e privacidade

- consultas filtram sempre por `recipient=request.user`;
- detalhe de outro usuário retorna 404;
- o cliente usa apenas UUID público;
- metadados aceitam somente chaves administrativas autorizadas;
- mensagens devem ser resumos e não conteúdo de prontuário, diagnóstico, CPF ou documento;
- URLs internas são produzidas pelo backend e não executam HTML;
- ações em massa possuem rate limiting e auditoria quando aplicável.

## Entrega assíncrona

`send_notification_delivery` usa Celery com retry exponencial, limite de tentativas e erro sanitizado. `cleanup_expired_notifications` arquiva notificações expiradas ou antigas conforme retenção configurada.

## Frontend

- sino no cabeçalho com contador `99+`;
- dropdown recente;
- rota `/dashboard/notificacoes`;
- abas Todas, Não lidas e Arquivadas;
- filtros de categoria, prioridade e pesquisa;
- leitura, retorno para não lida e arquivamento;
- paginação;
- preferências dentro de Configurações;
- polling de 60 segundos, pausa natural pelo TanStack Query e atualização ao focar a janela.

## Limitações

- WhatsApp exige provedor oficial e consentimento; permanece desabilitado;
- push exige cadastro de dispositivo e service worker; permanece desabilitado;
- não existe tenant de clínica no modelo atual, portanto o isolamento é por usuário/destinatário;
- resumo diário está persistido para evolução posterior, mas não possui agregador próprio nesta entrega.
