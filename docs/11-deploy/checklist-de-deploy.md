# Checklist de deploy

## Antes

- [ ] branch e SHA aprovados;
- [ ] testes, lint, build e security checks aprovados;
- [ ] migrations revisadas e backup disponível;
- [ ] settings de produção selecionado;
- [ ] segredos fortes/distintos no secret manager;
- [ ] Asaas produção e webhook configurados;
- [ ] banco, Redis e Blob privados;
- [ ] frontend compilado com URL correta da API;
- [ ] CORS/CSRF/hosts/domínios definidos;
- [ ] worker configurado;
- [ ] rollback e responsáveis definidos.

## Ordem sugerida

1. criar backup/restore point;
2. aplicar infraestrutura/configuração sem segredo em imagem;
3. executar migrations uma vez;
4. publicar API;
5. publicar worker;
6. publicar frontend;
7. configurar/validar webhook;
8. executar smoke tests;
9. observar logs e métricas;
10. registrar SHA e resultado.

## Smoke tests

- health do banco;
- login/refresh/logout com conta de teste;
- leitura de perfil;
- CRUD mínimo de paciente fictício;
- criação de agenda sem conflito;
- job de exportação fictício;
- acesso a arquivo temporário;
- preview de checkout sandbox apenas em staging;
- webhook de teste idempotente;
- admin restrito.

## Depois

Não use dados reais no smoke test. Remova dados fictícios e confirme que nenhuma chave apareceu nos logs.

[Voltar](README.md)
