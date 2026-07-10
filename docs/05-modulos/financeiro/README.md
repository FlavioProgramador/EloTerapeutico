# Módulo financeiro

**Status: implementado.**

## Finalidade

Controlar receitas, despesas e mensalidades da atividade do profissional. Este domínio é diferente do billing da assinatura do Elo Terapêutico.

## Entidades

### FinancialTransaction

- proprietário `therapist`;
- paciente, consulta e mensalidade opcionais;
- tipo `income` ou `expense`;
- categorias operacionais;
- origem manual, sessão, mensalidade ou recorrência;
- valor, valor pago, método e status;
- vencimento, pagamento, descrição, beneficiário, links;
- recorrência e período final.

Status de pagamento: `paid`, `partial`, `pending`, `cancelled`, `refunded`.

### MonthlySubscription

Representa mensalidade de paciente no contexto financeiro, não o plano SaaS. Seus detalhes são definidos no model correspondente.

## Regras de negócio

- valor deve ser positivo;
- valor pago não pode ser negativo nem superar o total;
- recorrência exige frequência;
- pagamento só ocorre em pendente/parcial;
- cancelamento só ocorre em pendente/parcial;
- estorno só ocorre em pago;
- pagamento parcial mantém status parcial;
- pagamento integral vinculado pode confirmar consulta agendada;
- resumo mensal soma apenas receitas/despesas pagas e separa pendências.

## API

O router está em `/api/v1/financeiro/`. Além de CRUD, actions em `api/actions/` tratam:

- listas e filtros;
- estados;
- pagamentos;
- mensalidades;
- relatórios;
- resumos de dashboard;
- ligação com billing quando aplicável.

Use o schema OpenAPI para nomes exatos das actions da revisão em execução.

## Frontend

`features/financeiro` possui dashboard, modal de transação e modal de mensalidade. Valores devem ser enviados como decimal válido e formatados na interface sem alterar a precisão do backend.

## Permissões e segurança

Transações pertencem ao terapeuta. Dados financeiros não devem ser misturados entre usuários. Links externos precisam ser validados e dados de pagamento não devem ser registrados em logs.

## Testes

Há testes de financeiro, mensalidades, dashboard, cobertura e performance.

## Limitações

- não substitui contabilidade ou conciliação bancária;
- não há garantia de integração automática de toda cobrança Asaas com o financeiro clínico;
- regras fiscais e emissão de nota não estão comprovadas;
- relatórios dependem da qualidade dos lançamentos.

[Voltar aos módulos](../README.md)
