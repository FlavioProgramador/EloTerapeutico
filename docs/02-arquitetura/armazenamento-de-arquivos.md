# Armazenamento de arquivos

## Tipos armazenados

- avatares;
- fotos de pacientes;
- documentos clínicos;
- anexos de evoluções;
- exportações de prontuário;
- PDFs de documentos gerados.

## Desenvolvimento

O storage padrão é o filesystem sob `MEDIA_ROOT`. Isso é adequado para desenvolvimento local, não para instâncias efêmeras ou múltiplas réplicas.

## Produção

Quando `AZURE_STORAGE_CONNECTION_STRING` está definida, o settings de produção usa Azure Storage com:

- container configurável;
- nomes sem sobrescrita;
- URLs temporárias;
- integração por django-storages.

`PRIVATE_MEDIA_STORAGE_REQUIRED=True` impede a inicialização sem Azure. Essa variável deve ser obrigatória para ambientes com dados reais.

## Requisitos operacionais

- container privado;
- criptografia e controle de acesso da plataforma;
- política de retenção coerente com o banco;
- backup/versionamento conforme criticidade;
- varredura antimalware ou quarentena;
- proibição de URLs públicas permanentes;
- teste de restauração e expiração de links.

## Limitação

A validação de upload clínico verifica tamanho, extensão, MIME declarado e assinatura real. Ela não executa antivírus.

[Voltar](README.md)
