# Checklist de Pull Request

## Escopo

- [ ] objetivo único e descrito;
- [ ] sem código não relacionado;
- [ ] sem segredo/dado real;
- [ ] compatibilidade e rollback explicados.

## Backend

- [ ] autorização e isolamento;
- [ ] validações/constraints;
- [ ] migrations revisadas;
- [ ] auditoria e logs mínimos;
- [ ] testes positivos e negativos;
- [ ] performance/queries avaliadas.

## Frontend

- [ ] loading/error/empty/success;
- [ ] acessibilidade e responsividade;
- [ ] sem confiança em role cliente;
- [ ] lint, typecheck, tests e build;
- [ ] screenshots fictícias.

## Segurança e dados

- [ ] threat model atualizado quando necessário;
- [ ] uploads/downloads/exports revisados;
- [ ] dados minimizados;
- [ ] variáveis documentadas;
- [ ] dependências auditadas;
- [ ] LGPD/retention avaliadas.

## Documentação

- [ ] módulo;
- [ ] API;
- [ ] caso de uso;
- [ ] ADR quando decisão estrutural;
- [ ] troubleshooting quando aplicável;
- [ ] links relativos válidos.

## Resultado dos checks

Registre comando, ambiente, SHA e resultado. Não escreva apenas “testado”.

[Voltar](README.md)
