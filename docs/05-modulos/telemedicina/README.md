# Telemedicina

**Situação:** implementada no código e condicionada à configuração operacional do LiveKit, HTTPS/WSS e validação em staging.

## Finalidade

A telemedicina permite atendimento remoto individual vinculado a uma consulta da Agenda. O MVP suporta exatamente um profissional e um paciente, nas modalidades `online` e `hybrid`.

O domínio permanece dentro de `apps.scheduling`. O LiveKit é tratado como integração substituível e não aparece diretamente nas views ou regras clínicas.

## Arquitetura

```text
Agenda/Appointment
  → TelemedicineRoom
  → services de sala, convite e consentimento
  → TelemedicineProvider
  → LiveKit
```

Camadas principais:

```text
backend/apps/scheduling/models/remote.py
backend/apps/scheduling/selectors/telemedicine.py
backend/apps/scheduling/services/telemedicine_*.py
backend/apps/scheduling/integrations/telemedicine/
backend/apps/scheduling/api/views/telemedicine.py
frontend/src/features/telemedicine/
```

## Entidades

- `TelemedicineRoom`: sala técnica única por consulta;
- `TelemedicineInvitation`: convite público armazenado somente como hash;
- `TelemedicineConsent`: aceite versionado do termo;
- `TelemedicineParticipantSession`: entrada e saída operacional, sem conteúdo clínico;
- `TelemedicineWebhookEvent`: idempotência dos eventos do provedor.

Áudio, vídeo, transcrição e gravação não são armazenados.

## Fluxo do profissional

1. O profissional acessa a Agenda autenticado.
2. Gera, envia ou revoga o convite do paciente.
3. Abre a rota autenticada da sala.
4. O backend valida organização, capability, profissional responsável, plano, configuração, estado e janela de entrada.
5. É emitido um JWT LiveKit de curta duração.
6. O navegador configura E2EE antes de conectar.
7. A conclusão técnica da sala não conclui automaticamente o atendimento clínico.

## Fluxo do paciente

1. O paciente recebe um link com token no fragmento `#token=`.
2. O navegador lê o fragmento e o remove imediatamente da URL.
3. O token é trocado por contexto mínimo via BFF.
4. O paciente aceita o termo versionado.
5. Testa câmera e microfone.
6. Recebe credenciais efêmeras e entra na sala.
7. Ao sair, tracks, sala, worker e credenciais em memória são liberados.

O token não é salvo em `localStorage`, `sessionStorage`, cookies acessíveis por JavaScript ou IndexedDB.

## E2EE

Cada sala recebe uma chave aleatória própria, criptografada em repouso pelo campo seguro já utilizado no backend. A chave é devolvida somente na emissão de credenciais e permanece em memória no navegador. Quando `TELEMEDICINE_REQUIRE_E2EE=True`, a conexão é bloqueada se a proteção não puder ser inicializada.

## Integrações

- **Agenda:** criação, reagendamento, alteração de modalidade, cancelamento, falta e conclusão;
- **Billing:** entitlement `has_telemedicine` nos planos Profissional e Premium;
- **Comunicações:** templates e fila persistente para convite por e-mail ou WhatsApp manual;
- **Auditoria:** geração, revogação, entrada e encerramento;
- **Celery Beat:** expiração periódica de salas e convites.

## Limitações deliberadas

Não fazem parte do MVP:

- chamadas em grupo;
- gravação;
- transcrição;
- resumo por IA;
- chat persistente;
- compartilhamento de tela;
- upload de documentos durante a chamada.

## Antes da produção

- configurar LiveKit Cloud ou infraestrutura validada;
- usar HTTPS e WSS;
- registrar webhook assinado;
- validar CSP no domínio final;
- executar smoke test com dois navegadores reais;
- configurar monitoramento e alertas de consumo;
- revisar termo, política de privacidade e protocolos clínicos com responsáveis jurídicos e profissionais.

A implementação técnica não representa certificação jurídica automática.
