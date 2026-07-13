# Checklist de segurança para produção

## Identidade

- [ ] cookies/tokens redesenhados para reduzir risco XSS;
- [ ] MFA para staff e acesso de infraestrutura;
- [ ] roles, grupos e permissões revisados;
- [ ] processo de entrada, mudança e desligamento;
- [ ] rate limit atrás de Redis confiável;
- [ ] reset de senha com SMTP e domínio corretos.

## Aplicação

- [ ] `DJANGO_SETTINGS_MODULE=config.settings.production`;
- [ ] DEBUG falso;
- [ ] hosts, CORS e CSRF explícitos;
- [ ] TLS/HSTS validados sem loop de proxy;
- [ ] CSP definida e testada;
- [ ] admin/SQL Explorer restritos;
- [ ] OpenAPI público avaliado;
- [ ] aliases/rotas legadas revisados.

## Dados

- [ ] tenant/clínica resolvido ou escopo individual formalizado;
- [ ] PostgreSQL privado, TLS e menor privilégio;
- [ ] Azure container privado;
- [ ] `PRIVATE_MEDIA_STORAGE_REQUIRED=True`;
- [ ] backups criptografados e restauração testada;
- [ ] retenção/exclusão definidas;
- [ ] rotação de chave testada;
- [ ] antivírus/quarentena de uploads.

## Integrações

- [ ] Asaas produção, API key e webhook token;
- [ ] webhook idempotente e monitorado;
- [ ] SMTP protegido;
- [ ] Redis com autenticação/TLS quando aplicável;
- [ ] URLs temporárias de storage com expiração curta.

## Qualidade

- [ ] pytest, check e migration check aprovados;
- [ ] lint/typecheck/build frontend aprovados;
- [ ] Bandit e pip-audit aprovados;
- [ ] dependências e imagens escaneadas;
- [ ] testes de permissão/IDOR;
- [ ] pentest do artefato final;
- [ ] smoke test pós-deploy;
- [ ] plano de rollback.

## Operação

- [ ] logs centralizados e sem dados sensíveis;
- [ ] alertas de 5xx, auth, fila, banco, storage e webhook;
- [ ] runbooks e contatos;
- [ ] resposta a incidentes exercitada;
- [ ] inventário e bases legais revisados.

[Voltar](README.md)
