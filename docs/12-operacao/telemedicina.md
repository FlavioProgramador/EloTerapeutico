# Operação da telemedicina

O projeto utiliza a seção `12-operacao`, preservando a numeração existente do portal técnico.

## Variáveis

```text
TELEMEDICINE_ENABLED=False
TELEMEDICINE_PROVIDER=livekit
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
TELEMEDICINE_REQUIRE_E2EE=True
TELEMEDICINE_JOIN_BEFORE_MINUTES=15
TELEMEDICINE_JOIN_AFTER_MINUTES=30
TELEMEDICINE_PROVIDER_TOKEN_TTL_SECONDS=300
TELEMEDICINE_EMPTY_ROOM_TIMEOUT_SECONDS=300
TELEMEDICINE_MAX_PARTICIPANTS=2
TELEMEDICINE_MAINTENANCE_INTERVAL_SECONDS=300
```

A aplicação inicia normalmente com o módulo desligado. Quando ativado sem configuração completa, o Django system check retorna erro e a API falha de forma segura.

## Configuração em staging

1. Criar projeto separado no LiveKit Cloud.
2. Obter URL WSS, API key e API secret.
3. Registrar os segredos no cofre do ambiente, nunca no Git.
4. Configurar `LIVEKIT_URL` também no processo de build do frontend para gerar a CSP correta.
5. Configurar o webhook para:

```text
https://staging.example/api/v1/scheduling/integrations/livekit/webhook/
```

6. Executar migrations.
7. Reiniciar backend, frontend, Celery worker e Celery Beat.
8. Executar `python manage.py check`.
9. Habilitar telemedicina na organização de teste.
10. Executar smoke test com dois navegadores.
11. Somente depois definir `TELEMEDICINE_ENABLED=True` no ambiente comercial.

## Processos necessários

- backend Django;
- frontend Next.js;
- PostgreSQL;
- Redis;
- Celery worker `default`;
- Celery Beat;
- serviço LiveKit acessível por WSS.

A tarefa `apps.scheduling.tasks.expire_stale_telemedicine_rooms` deve aparecer no Beat.

## Monitoramento

Monitorar sem PII:

- tentativas e falhas de entrada;
- erros do provider;
- webhooks rejeitados;
- salas presas em `waiting` ou `in_progress`;
- atraso do Celery Beat;
- consumo de minutos e transferência do LiveKit;
- falhas de câmera, microfone e E2EE reportadas pelo frontend.

Não usar room name, convite, paciente, e-mail ou appointment ID como label de alta cardinalidade.

## Diagnóstico

### Módulo indisponível

Verificar:

- `TELEMEDICINE_ENABLED`;
- credenciais LiveKit;
- entitlement do plano;
- `allow_telemedicine` da organização;
- status da assinatura;
- system checks.

### Paciente não entra

Verificar:

- convite ativo e não expirado;
- janela de entrada;
- consentimento;
- status e modalidade da consulta;
- relógio e timezone;
- bloqueios de câmera/microfone no navegador.

### Profissional não entra

Verificar:

- organização ativa selecionada;
- membership e capability;
- profissional responsável;
- assinatura do proprietário da organização;
- sala não cancelada ou finalizada.

### Webhook não processa

Verificar URL, secret, header `Authorization`, relógio, reachability e eventos duplicados. O payload bruto não deve ser incluído em tickets ou logs de suporte.

## Contingência

Em indisponibilidade do provedor:

- não fazer fallback para chamada sem E2EE;
- informar indisponibilidade de forma genérica;
- usar o canal alternativo definido pela organização;
- reagendar ou encaminhar para atendimento presencial quando adequado;
- registrar apenas o incidente operacional necessário.

## Rollback

1. definir `TELEMEDICINE_ENABLED=False`;
2. manter migrations e dados históricos;
3. reiniciar serviços;
4. revogar convites ativos se necessário;
5. confirmar que consultas e demais módulos continuam operando;
6. não executar migration destrutiva durante incidente.
