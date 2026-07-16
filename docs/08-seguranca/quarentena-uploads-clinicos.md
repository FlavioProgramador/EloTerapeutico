# Quarentena de uploads clínicos

## Objetivo

Nenhum arquivo enviado ao prontuário fica disponível para download antes de concluir validação estrutural e análise antimalware.

```text
Upload
→ validação de tamanho, extensão, MIME e assinatura
→ storage de quarentena
→ fila Celery `uploads`
→ ClamAV INSTREAM
→ storage privado liberado ou rejeição
```

## Estados

| Estado | Download | Arquivo |
| --- | --- | --- |
| `pending` | bloqueado | quarentena |
| `scanning` | bloqueado | quarentena |
| `clean` | permitido, sujeito à autorização | storage clínico privado |
| `infected` | bloqueado | bytes removidos |
| `failed` | bloqueado | quarentena até retry/retention |

A API retorna `202 Accepted` no upload. O frontend deve atualizar a listagem até o estado final e nunca construir URLs de storage.

## Configuração

```text
CLINICAL_UPLOAD_SCANNER_BACKEND=clamd
CLAMAV_HOST=clamav.internal
CLAMAV_PORT=3310
CLAMAV_TIMEOUT_SECONDS=15
CLAMAV_STREAM_CHUNK_BYTES=65536
CLINICAL_SCAN_MAX_ATTEMPTS=3
CLINICAL_SCAN_DISPATCH_BATCH_SIZE=20
CLINICAL_SCAN_DISPATCH_INTERVAL_SECONDS=20
CLINICAL_SCAN_PROCESSING_TIMEOUT_MINUTES=5
CLINICAL_SCAN_RECOVERY_INTERVAL_SECONDS=120
CLINICAL_QUARANTINE_RETENTION_HOURS=24
```

Mocks existem apenas para testes automatizados e exigem `CLINICAL_UPLOAD_SCANNER_ALLOW_MOCK=true`. O system check rejeita mock ou scanner desabilitado em produção.

## Filas e tarefas

- `apps.records.tasks.scan_clinical_document`;
- `apps.records.tasks.dispatch_pending_document_scans`;
- `apps.records.tasks.recover_stuck_document_scans`;
- `apps.records.tasks.cleanup_rejected_clinical_documents`.

Execute ao menos um worker consumindo a fila `uploads`. O Celery Beat recupera pendências, jobs interrompidos e arquivos que atingiram a retenção.

## Segurança operacional

- ClamAV deve ficar em rede privada;
- não exponha a porta 3310 à internet;
- atualize assinaturas de malware regularmente;
- monitore indisponibilidade, latência e taxa de rejeição;
- não registre nome, conteúdo, CPF, descrição clínica ou assinatura detectada completa;
- o prefixo `clinical_quarantine/` deve ser privado e não possuir URL pública;
- o prefixo liberado também permanece privado e exige endpoint autenticado;
- scanner indisponível resulta em falha segura: o arquivo continua bloqueado.

## Resposta a incidentes

1. interrompa downloads se houver suspeita de bypass;
2. preserve somente metadados mínimos e IDs técnicos;
3. isole o storage de quarentena;
4. atualize assinaturas do scanner;
5. reprocesse itens falhos dentro do limite configurado;
6. descarte bytes infectados e confirme a remoção;
7. revise logs sanitizados, permissões e origem do upload;
8. comunique responsáveis conforme o plano de incidentes e a política LGPD.

## Rollback

Não reverta para liberação imediata. Em caso de falha do scanner, mantenha os documentos em `failed` ou `pending` e restaure o serviço. Reverter o schema só é seguro após remover referências e arquivos de quarentena em ambiente autorizado.

[Voltar](README.md)
