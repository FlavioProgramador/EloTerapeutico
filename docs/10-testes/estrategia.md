# Estratégia de testes

## Pirâmide recomendada

1. unitários para validators, transitions e serviços puros;
2. integração Django/DRF para banco, permissions e endpoints;
3. contrato para frontend/API e gateways simulados;
4. componentes e hooks frontend;
5. E2E para fluxos críticos;
6. segurança, performance e smoke tests.

## Fluxos críticos

- login, refresh, logout e reset;
- isolamento entre usuários;
- secretária sem prontuário;
- conteúdo confidencial;
- janela de 48 horas e aditivos;
- upload e download autorizados;
- worker e retries;
- conflitos de agenda;
- pagamentos/estornos;
- geração de documentos;
- webhook idempotente;
- storage e links temporários.

## Dados de teste

Factories/Faker podem ser usados, sempre com dados fictícios. Nunca copie dump ou caso clínico real. Arquivos de teste devem ser mínimos e seguros.

## Gates

- testes aprovados;
- migrations sem mudanças pendentes;
- lint e typecheck;
- build frontend;
- Bandit/pip-audit;
- revisão de diff e segredos;
- testes específicos de permissão quando o contrato muda.

[Voltar](README.md)
