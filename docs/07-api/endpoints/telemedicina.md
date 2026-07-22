# API de telemedicina

Prefixo: `/api/v1/scheduling/`.

Todas as respostas com convite, JWT ou chave E2EE usam `Cache-Control: no-store`.

## Endpoints autenticados

| Método | Rota | Finalidade |
| --- | --- | --- |
| `GET` | `telemedicine/` | Lista salas do tenant sem tokens ou IDs internos do provedor |
| `GET` | `telemedicine/{id}/` | Detalha estado operacional da sala |
| `POST` | `telemedicine/{id}/create-invitation/` | Revoga convite anterior e devolve um novo link uma única vez |
| `POST` | `telemedicine/{id}/send-invitation/` | Cria convite novo e o enfileira em Comunicações |
| `POST` | `telemedicine/{id}/revoke-invitation/` | Revoga o convite ativo |
| `POST` | `telemedicine/{id}/join-professional/` | Emite credenciais efêmeras do profissional |
| `POST` | `telemedicine/{id}/finish/` | Fecha a sala técnica e revoga acessos |
| `POST` | `telemedicine/{id}/remove-participant/` | Remove uma identidade pertencente à sala |
| `GET` | `telemedicine/{id}/status/` | Consulta estado e participantes ativos |

O endpoint `open-room` permanece temporariamente como alias de `join-professional`. Links profissionais públicos deixaram de ser emitidos.

### Criar convite

Resposta `201`:

```json
{
  "invitation_url": "https://app.example/consulta-online/paciente#token=...",
  "expires_at": "2026-07-22T15:00:00-03:00"
}
```

O valor puro do convite não aparece na listagem e não é persistido em texto legível.

### Enviar convite

```json
{
  "channel": "email"
}
```

Canais aceitos no MVP:

- `email`;
- `whatsapp_manual`.

Resposta `202` contém somente ID administrativo, canal e status da fila; não contém o link.

## Endpoints públicos via BFF

| Método | Rota | Finalidade |
| --- | --- | --- |
| `POST` | `telemedicine/public/exchange/` | Troca o convite por contexto mínimo |
| `POST` | `telemedicine/public/consent/` | Registra aceite versionado |
| `POST` | `telemedicine/public/join/` | Emite credenciais efêmeras do paciente |
| `POST` | `telemedicine/public/leave/` | Remove a conexão do paciente |

Essas rotas:

- não usam autenticação JWT da aplicação;
- exigem origem confiável no BFF;
- possuem rate limit por IP;
- não retornam prontuário, CPF, telefone, e-mail, observações ou dados financeiros;
- retornam mensagens genéricas para acessos inválidos ou expirados.

## Webhook

```text
POST /api/v1/scheduling/integrations/livekit/webhook/
```

O corpo bruto e o header `Authorization` são verificados pelo SDK do LiveKit. Eventos suportados:

- `room_started`;
- `room_finished`;
- `participant_joined`;
- `participant_left`;
- `participant_connection_aborted`.

O processamento é idempotente por `provider + provider_event_id`. O payload bruto não é armazenado.

## Erros públicos

| Situação | Status típico |
| --- | --- |
| convite expirado ou revogado | `410` |
| consentimento ausente | `428` |
| fora da janela de entrada | `403` |
| sem permissão | `403` |
| estado incompatível | `409` |
| módulo ou provedor indisponível | `503` |
| assinatura do webhook inválida | `401` |
