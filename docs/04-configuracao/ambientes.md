# Ambientes

## Desenvolvimento — `config.settings.development`

- DEBUG ativo;
- CORS aberto;
- SQLite como fallback;
- e-mail no console;
- rate limiting desabilitado;
- Debug Toolbar instalada.

Não exponha esse settings à internet.

## Teste — `config.settings.test`

- SQLite dedicado;
- hasher MD5 para velocidade;
- e-mail em memória;
- storage em diretório de teste;
- CORS e rate limit desativados;
- limites de pacientes por plano desabilitados.

Nunca use esse settings para dados reais.

## Produção — `config.settings.production`

- DEBUG desativado;
- hosts e CORS explícitos;
- segredos fortes e distintos;
- HTTPS redirect, HSTS e headers;
- cookies Django seguros;
- PostgreSQL com conexões persistentes;
- Redis para cache;
- WhiteNoise para estáticos;
- Azure Blob opcional e storage privado exigível;
- logging JSON;
- SMTP/TLS;
- Asaas de produção obrigatório e sandbox proibido.

## Seleção

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```

No Windows PowerShell:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.production"
```

[Voltar](README.md)
