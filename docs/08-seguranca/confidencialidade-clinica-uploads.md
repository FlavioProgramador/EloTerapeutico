# Confidencialidade clínica e uploads

## Conteúdo clínico

`EncryptedTextField` cifra texto com Fernet após derivar uma chave SHA-256 da variável configurada. Valores persistidos recebem versão `v1:` ou `v2:`. Falha de descriptografia retorna marcador de dado inacessível.

### Escopo

A criptografia é aplicada a campos selecionados, como conteúdo de evolução, aditivos e snapshots documentais. Ela não equivale a criptografia automática de todas as colunas, banco, backups ou logs.

### Confidencialidade

- evolução comum: visível conforme acesso ao prontuário;
- evolução confidencial: autor ou permissão explícita;
- exportação confidencial: permissão específica;
- admins não devem receber acesso clínico apenas por papel global;
- worker filtra evoluções conforme permissão do solicitante.

## Sanitização de conteúdo

- normalização Unicode NFC;
- remoção de controles;
- remoção de tags HTML;
- remoção de esquemas `javascript`, `vbscript` e `data`;
- remoção de handlers `on*`;
- limite configurável de tamanho;
- renderização segura posterior para PDF.

## Uploads clínicos

### Implementado

- tamanho maior que zero;
- máximo padrão de 10 MB;
- até dez anexos por evolução por padrão;
- extensões JPEG/JPG, PNG, GIF, WebP e PDF;
- MIME declarado coerente;
- magic bytes coerentes;
- nome de exibição sanitizado;
- paths controlados e storage abstrato.

### Pendente

- antivírus/antimalware;
- quarentena e análise assíncrona;
- Content Disarm and Reconstruction para PDFs, quando exigido;
- limites no proxy e storage;
- classificação e retenção por tipo;
- validação de imagens além do cabeçalho.

## Rotação de chave

1. introduzir `FIELD_ENCRYPTION_KEY_V2`;
2. testar leitura de v1 e escrita de v2;
3. criar migration/command transacional de recriptografia;
4. verificar contagem e backups;
5. manter v1 até confirmar migração;
6. revogar chave antiga apenas após restauração testada.

[Voltar](README.md)
