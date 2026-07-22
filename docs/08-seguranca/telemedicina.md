# Segurança da telemedicina

## Modelo de confiança

O backend é a fonte de verdade. Ocultar botões no frontend não concede nem retira acesso.

A emissão de credenciais combina:

```text
feature flag global
+ provedor configurado
+ configuração da organização
+ entitlement da assinatura
+ membership e capability
+ vínculo com o profissional
+ modalidade e status da consulta
+ janela de entrada
+ consentimento do paciente
```

## Convites

- gerados com alta entropia;
- persistidos somente como SHA-256;
- um convite ativo por sala e papel;
- revogados ao regenerar, cancelar, expirar ou finalizar;
- entregues no fragmento da URL, não em query string;
- removidos da barra de endereço antes da troca;
- nunca incluídos em logs ou listagens.

## Credenciais de mídia

- JWT emitido exclusivamente no backend;
- room grant limitado à sala correspondente;
- TTL padrão de cinco minutos;
- identidade opaca sem nome, e-mail, CPF ou ID sequencial isolado;
- sem grants de gravação, egress ou administração;
- não persistido no banco nem em storage do navegador.

## Criptografia ponta a ponta

A chave E2EE é aleatória por sala e armazenada com o campo criptografado do projeto. O navegador recebe a chave somente após autorização e a mantém em memória. A sala usa o worker oficial de E2EE do cliente LiveKit.

Não existe fallback silencioso para mídia sem E2EE quando a proteção é obrigatória.

## Headers

O frontend configura:

- `Content-Security-Policy` sem curingas em `connect-src`;
- host LiveKit obtido da configuração operacional;
- `Permissions-Policy: camera=(self), microphone=(self)`;
- `display-capture=()`;
- `Referrer-Policy: no-referrer`;
- `X-Frame-Options: DENY`;
- `X-Content-Type-Options: nosniff`.

Respostas de credenciais usam `Cache-Control: no-store` e `Pragma: no-cache`.

## Webhook

- assinatura validada pelo SDK;
- corpo bruto usado apenas para verificação e hash;
- idempotência por identificador do provedor;
- tolerância a reenvio;
- eventos não concluem automaticamente o prontuário ou a consulta;
- payload bruto não é persistido.

## Dados proibidos no provedor

Não enviar em room name, identity, metadata ou attributes:

- nome do paciente;
- nome do profissional;
- e-mail;
- CPF;
- telefone;
- diagnóstico;
- observações da consulta;
- conteúdo do prontuário;
- dados financeiros.

## Gravação

O MVP não instala nem utiliza Egress, `MediaRecorder`, transcrição, reconhecimento de fala ou captura automática de tela.

## Checklist de produção

- HTTPS e HSTS no domínio final;
- WSS válido para LiveKit;
- segredos independentes e rotacionáveis;
- webhook assinado configurado;
- CSP validada no navegador;
- monitoramento de erros e consumo sem PII;
- testes com redes e dispositivos reais;
- revisão de retenção, privacidade e resposta a incidentes.
