# ADR-005 — Storage abstrato com Azure Blob opcional

## Status
Aceita com requisito operacional pendente.

## Data
10/07/2026.

## Contexto
Documentos e anexos não podem depender de disco efêmero em produção e exigem acesso privado.

## Decisão
Usar storage Django: filesystem no desenvolvimento e AzureStorage quando connection string é configurada. `PRIVATE_MEDIA_STORAGE_REQUIRED` pode impedir fallback.

## Alternativas consideradas
Motivação inferida. Alternativas: S3, volume persistente, banco ou serviço dedicado.

## Consequências positivas
- API de storage uniforme;
- URLs temporárias;
- escalabilidade e persistência do Blob;
- desenvolvimento simples localmente.

## Consequências negativas
- configuração e custo externos;
- conexão por segredo quando identidade gerenciada não é usada;
- fallback local pode mascarar erro;
- backup banco/storage precisa ser coordenado.

## Riscos
Produção iniciar com filesystem local. Recomendação: tornar a flag obrigatória e validar container privado.

## Referências no código
`settings/prod.py`, `backend/.env.example`.

[Voltar](README.md)
