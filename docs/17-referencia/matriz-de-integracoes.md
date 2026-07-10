# Matriz de integrações

| Integração | Uso | Configuração | Dados | Situação | Riscos |
| --- | --- | --- | --- | --- | --- |
| Asaas | billing, cobrança e webhook | API key, URL, token | identidade, cobrança, IDs | Implementado/configurável | indisponibilidade, webhook falso |
| Azure Blob | arquivos privados | connection string, container | documentos/anexos | Parcial/configurável | exposição, perda, segredo |
| SMTP/SendGrid | reset de senha | host, user, password | e-mail e link temporário | Configurável | entrega, token em log |
| PostgreSQL | persistência principal | DATABASE_URL | todos os domínios | Implementado | acesso, backup, locks |
| Redis | cache/rate limit em prod | REDIS_URL | chaves técnicas | Configurável | indisponibilidade, rede |
| WeasyPrint | geração de PDF | libs nativas | conteúdo renderizado | Implementado | SSRF/renderização/erro nativo |
| OpenAPI | documentação da API | drf-spectacular | contrato técnico | Implementado | exposição excessiva |
| IA clínica | resumo/status | não comprovada | potencialmente clínicos | Não configurada/planejada | privacidade e decisão indevida |

[Voltar](README.md)
