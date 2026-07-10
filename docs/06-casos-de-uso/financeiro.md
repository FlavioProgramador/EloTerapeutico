# Casos de uso — Financeiro

# UC-FIN-001 — Registrar transação

## Objetivo
Registrar receita ou despesa pertencente ao terapeuta.

## Atores
Terapeuta autorizado.

## Pré-condições
Usuário autenticado; referências acessíveis.

## Fluxo principal
1. Usuário informa tipo, categoria, valor, vencimento e descrição.
2. Pode vincular paciente, consulta ou mensalidade.
3. API valida valor e recorrência.
4. Transação nasce normalmente pendente e com origem definida.

## Exceções
Valor não positivo, pagamento superior ao total ou frequência ausente.

## Dados envolvidos
Valores, datas, método, paciente, beneficiário e links.

## Regras de segurança
Owner obrigatório; precisão decimal; nenhum dado bruto de cartão.

## Endpoints relacionados
Router `/api/v1/financeiro/`.

## Testes relacionados
Suítes de financeiro e performance.

## Status de implementação
Implementado.

---

# UC-FIN-002 — Registrar pagamento

## Fluxo principal
1. Usuário seleciona transação pendente/parcial.
2. Informa método e valor pago.
3. Backend impede valor inválido.
4. Status vira parcial ou pago.
5. Se integral e ligado a consulta agendada, consulta pode virar confirmada.

## Exceções
Transação cancelada, estornada ou já paga não aceita novo pagamento.

## Status de implementação
Implementado.

---

# UC-FIN-003 — Cancelar ou estornar

Cancelamento é permitido em pendente/parcial; estorno somente em pago. As ações não devem apagar histórico.

## Status de implementação
Implementado.

[Voltar](README.md)
