# Resposta a falhas

| Sintoma | Diagnóstico | Ação inicial |
| --- | --- | --- |
| API não inicia | settings, segredo, migration, banco | revisar logs sem expor valores |
| Health 503 | conexão/credencial do banco | testar DNS, porta e pool |
| Frontend não acessa API | URL, CORS, TLS, build env | validar `NEXT_PUBLIC_API_URL` |
| Login falha geral | JWT secret, banco, clock | conferir settings e horário |
| Muitos 401 | access expirado/refresh | revisar rotação e cookies |
| Exportação pendente | worker parado | iniciar worker e ver idade da fila |
| Exportação falha | WeasyPrint/storage/dado | revisar tipo de exceção e retry |
| Upload recusado | tamanho/MIME/magic bytes | corrigir arquivo, não desabilitar validação |
| Asaas 502 | key, URL, indisponibilidade | validar configuração e status do provedor |
| Webhook 403 | token divergente | sincronizar segredo e rotacionar com cuidado |
| Arquivo 404 | storage/metadata/permissão | verificar owner, blob e expiração |
| Banco lento | query, índice, locks, pool | analisar plano e métricas |

## Princípio

Não contorne segurança para recuperar serviço. Evite habilitar DEBUG, CORS aberto, webhook sem token, storage público ou permissões amplas em produção.

[Voltar](README.md)
