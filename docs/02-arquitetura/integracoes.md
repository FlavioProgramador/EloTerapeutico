# Integrações

## Asaas

**Status:** implementado; requer configuração operacional.

Usado para criar clientes, assinaturas e cobranças, consultar recursos, cancelar assinaturas e processar webhooks. O backend usa `httpx` e mapeia erros externos para mensagens públicas controladas.

Configuração: `ASAAS_API_KEY`, `ASAAS_BASE_URL` e `ASAAS_WEBHOOK_TOKEN`.

## Azure Blob Storage

**Status:** parcialmente implementado/configurável.

`prod.py` troca o storage padrão por `storages.backends.azure_storage.AzureStorage` quando há connection string. URLs expiram pelo valor de `AZURE_URL_EXPIRATION_SECS`.

O repositório não comprova que uma conta, container privado ou política de rede estejam implantados.

## SMTP

**Status:** configurável.

Desenvolvimento imprime e-mails no console. Produção usa SMTP/TLS, com host padrão do SendGrid e credenciais por variáveis.

## Redis

**Status:** configuração de produção.

Usado como cache e backend do rate limiting em `prod.py`. Não é a fila das exportações clínicas.

## WeasyPrint

**Status:** implementado.

Gera PDFs de prontuários e documentos. Requer bibliotecas nativas Pango. O worker contém fallback de teste quando a biblioteca não pode ser importada, o que não deve ser tratado como geração válida em produção.

[Voltar](README.md)
