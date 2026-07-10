# Azure

## Opções compatíveis

- Azure Static Web Apps ou App Service para frontend Next.js, conforme suporte ao modo usado;
- Azure App Service ou Container Apps para Django;
- processo separado em Container Apps/App Service WebJob/worker dedicado para exportações;
- Azure Database for PostgreSQL;
- Azure Cache for Redis ou serviço compatível;
- Azure Blob Storage privado;
- Key Vault;
- Application Insights/Log Analytics;
- Front Door/Application Gateway quando necessário.

## O que o repositório comprova

- settings `prod.py` declarado para Azure App Service;
- suporte a Azure Blob por django-storages;
- logging JSON;
- headers de proxy/TLS;
- variável opcional de IP do cliente Azure;
- Dockerfiles para frontend/backend.

## O que não comprova

- recursos Azure criados;
- IaC;
- domínio/TLS;
- rede privada;
- identidade gerenciada;
- pipeline de deploy;
- backup/alertas ativos;
- custos e dimensionamento.

## Azure for Students

Pode ser usada para ambiente de estudo, respeitando créditos e disponibilidade. Dados clínicos reais só devem ser usados após revisão contratual, segurança, privacidade, localização, backup e suporte — não apenas porque o recurso está disponível.

[Voltar](README.md)
