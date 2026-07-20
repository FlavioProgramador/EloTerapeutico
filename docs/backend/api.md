# API do backend

## URL base e versionamento

A API principal utiliza o prefixo:

```text
/api/v1/
```

Rotas de compatibilidade de billing também existem em `/api/billing/`. Novas integrações devem preferir o contrato versionado em `/api/v1/billing/`.

O domínio de calendário usa exclusivamente `/api/v1/scheduling/`. A antiga rota `/api/v1/agenda/` não é registrada.

## Grupos de endpoints

| Prefixo | Domínio |
| --- | --- |
| `/api/v1/auth/` | Autenticação, credenciais e perfil |
| `/api/v1/patients/` | Pacientes e responsáveis |
| `/api/v1/records/` | Prontuário e exportações clínicas |
| `/api/v1/scheduling/` | Consultas, recorrências, salas e pacotes |
| `/api/v1/financeiro/` | Financeiro operacional do terapeuta |
| `/api/v1/documents/` | Templates e documentos gerados |
| `/api/v1/reports/` | Indicadores e exportações |
| `/api/v1/forms/` | Templates, campos e submissões |
| `/api/v1/billing/` | Planos, assinatura, checkout e pagamentos |
| `/api/v1/communications/` | Comunicações, templates e automações |
| `/api/v1/public/communications/` | Links públicos controlados por token |

## Autenticação

Por padrão, endpoints protegidos exigem access token JWT:

```http
Authorization: Bearer <access-token>
```

A autenticação padrão também verifica as regras de acesso relacionadas à assinatura quando configuradas. Endpoints públicos devem declarar explicitamente a ausência de autenticação e limitar o acesso por token de uso específico, expiração e escopo.

## Métodos HTTP

- `GET`: leitura sem efeitos colaterais relevantes;
- `POST`: criação, comando ou ação não idempotente;
- `PUT`: substituição integral quando suportada;
- `PATCH`: atualização parcial;
- `DELETE`: exclusão, arquivamento ou cancelamento conforme o contrato do endpoint.

A documentação OpenAPI deve deixar claro quando `DELETE` executa exclusão lógica em vez de remover fisicamente o registro.

## Paginação

A configuração padrão usa `StandardResultsPagination` com página de 20 itens. Respostas paginadas devem seguir o contrato do paginador configurado pelo projeto e preservar links ou metadados esperados pelo frontend.

Parâmetros usuais:

```text
?page=1
?page_size=20
```

O limite máximo, quando definido pela classe de paginação, deve ser respeitado para evitar consultas excessivas.

## Filtros, busca e ordenação

O DRF está configurado com:

- `DjangoFilterBackend`;
- `SearchFilter`;
- `OrderingFilter`.

Cada ViewSet deve expor somente campos seguros e indexáveis. Filtros nunca substituem o isolamento obrigatório pelo usuário autenticado.

Exemplos comuns:

```text
?status=active
?search=nome
?ordering=-created_at
?date_from=2026-07-01&date_to=2026-07-31
```

Os nomes exatos dependem do endpoint e devem ser obtidos no schema OpenAPI.

## Cabeçalho de idempotência

O backend permite o header `Idempotency-Key` no CORS. Operações críticas, como checkout, pagamentos ou geração de recursos, devem documentar quando o header é aceito e como chaves repetidas são tratadas.

```http
Idempotency-Key: 6d4e1d68-48b1-4db0-bbc9-c94de53c54db
```

Uma chave de exemplo nunca deve ser reutilizada como segredo.

## Códigos HTTP

| Código | Uso esperado |
| --- | --- |
| `200 OK` | Leitura ou comando concluído |
| `201 Created` | Recurso criado |
| `202 Accepted` | Processamento persistido para execução assíncrona |
| `204 No Content` | Operação concluída sem corpo |
| `400 Bad Request` | Payload ou transição inválida |
| `401 Unauthorized` | Token ausente, inválido, expirado ou revogado |
| `403 Forbidden` | Usuário autenticado sem permissão ou assinatura necessária |
| `404 Not Found` | Recurso inexistente ou fora do escopo do usuário |
| `409 Conflict` | Concorrência, idempotência ou estado incompatível |
| `422 Unprocessable Entity` | Erro semântico quando adotado pelo endpoint |
| `429 Too Many Requests` | Limite de requisições excedido |
| `500 Internal Server Error` | Falha não tratada, sem exposição de detalhes internos |
| `502 Bad Gateway` | Falha de integração externa quando o contrato prevê essa tradução |

Recursos fora do escopo do usuário devem preferencialmente ser indistinguíveis de recursos inexistentes, evitando enumeração por identificador.

## Formato de erros

O projeto utiliza um exception handler customizado. Toda documentação de endpoint deve refletir o formato real retornado pelo handler e pelos serializers.

Exemplo genérico, não contratual:

```json
{
  "detail": "Não foi possível concluir a operação.",
  "code": "validation_error",
  "errors": {
    "field": ["Mensagem de validação."]
  }
}
```

Não inclua stack traces, nomes de tabelas, caminhos locais, tokens ou payloads integrais de providers.

## OpenAPI, Swagger e Redoc

Rotas disponíveis em desenvolvimento:

- schema: `/api/schema/`;
- Swagger UI: `/api/docs/`;
- Redoc: `/api/redoc/`.

Geração e validação:

```bash
cd backend
python manage.py spectacular --file schema.yml --validate
```

A documentação de cada endpoint deve cobrir:

- método e rota;
- autenticação e permissions;
- path e query parameters;
- request body;
- serializers de leitura e escrita;
- respostas de sucesso;
- erros esperados;
- paginação;
- filtros e ordenação;
- efeitos colaterais;
- regras de proprietário ou autoria.

## Uploads e downloads

Endpoints de arquivo devem documentar:

- extensões e MIME types aceitos;
- tamanho máximo;
- validação de assinatura do arquivo;
- vínculo com paciente ou documento;
- regras de acesso;
- expiração de URL temporária;
- comportamento quando o arquivo não existe no storage.

Downloads nunca devem confiar apenas no UUID recebido; o vínculo com o usuário deve ser validado antes de abrir o arquivo.

## Webhooks

Webhooks de billing ou comunicações devem:

1. validar token, assinatura ou segredo configurado;
2. persistir um identificador único do evento;
3. impedir processamento duplicado;
4. registrar status e tentativas sem armazenar segredos;
5. responder rapidamente e delegar processamento quando necessário;
6. manter um caminho de reconciliação para eventos perdidos.

## Compatibilidade

Mudanças na documentação não devem alterar:

- nomes de rotas canônicas;
- serializers públicos;
- códigos HTTP;
- campos obrigatórios;
- paginação;
- filtros;
- permissions;
- comportamento de idempotência.

Para scheduling, somente `/api/v1/scheduling/` é contrato público. O nome visual “Agenda” e o app label histórico `agenda` não criam uma segunda rota HTTP.
