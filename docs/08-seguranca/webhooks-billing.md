# Webhooks e billing

## Fluxo Asaas

- API key permanece no backend;
- endpoint de webhook não usa JWT;
- token é lido de headers compatíveis;
- comparação usa `secrets.compare_digest`;
- eventos são deduplicados por ID/hash;
- assinatura só deve ficar ativa após evento válido;
- respostas de checkout removem campos privados;
- funções de redaction mascaram chaves como token, CPF, cartão, CVV, API key e senha.

## Produção

`prod.py`:

- exige API key;
- rejeita URL contendo `sandbox`;
- exige webhook token forte;
- exige segredos diferentes de Django, JWT e criptografia.

## Riscos

- no desenvolvimento, webhook sem token é aceito com warning;
- replay precisa continuar idempotente em todas as versões de evento;
- URLs de fatura/boleto são pessoais;
- indisponibilidade do gateway gera 502 e exige retry controlado;
- não armazenar dados brutos de cartão;
- `raw_payload` deve permanecer sanitizado;
- logs de HTTP não podem incluir access token do Asaas.

## Checklist de webhook

- [ ] HTTPS público válido;
- [ ] token forte e exclusivo;
- [ ] segredo cadastrado no Asaas e no secret manager;
- [ ] endpoint limitado a POST;
- [ ] deduplicação testada;
- [ ] eventos desconhecidos tratados sem corromper estado;
- [ ] monitoramento de falhas/retries;
- [ ] reconciliação periódica com API do gateway;
- [ ] rotação de token testada;
- [ ] payload sensível ausente de logs.

[Voltar](README.md)
