# Casos de uso — Agenda

# UC-AGE-001 — Agendar consulta

## Objetivo
Criar sessão sem conflito de profissional, paciente, sala ou bloqueio.

## Atores
Terapeuta ou usuário administrativo autorizado.

## Pré-condições
Paciente e terapeuta acessíveis; horários válidos.

## Fluxo principal
1. Usuário escolhe paciente, data, duração, modalidade, tipo e valor.
2. API valida início/término e valor.
3. API verifica sobreposição de terapeuta, paciente/participantes, sala e bloqueios.
4. Consulta é criada como `scheduled`, salvo regra específica.
5. Interface atualiza o calendário.

## Fluxos alternativos
### A1 — Recorrência
É criada série semanal, quinzenal ou mensal e instâncias relacionadas.

### A2 — Sessão em grupo
Participantes adicionais são associados.

### A3 — Online
Não há sala física; fluxo de telemedicina pode ser criado.

## Exceções
Conflito, sala inativa, término inválido ou modalidade incompatível.

## Pós-condições
Consulta aparece na agenda e pode originar financeiro/evolução.

## Dados envolvidos
Paciente, participantes, profissional, horários, modalidade, notas e valor.

## Regras de segurança
Notas são administrativas; querysets devem ser isolados; tokens de telemedicina são secretos.

## Endpoints relacionados
`/api/v1/scheduling/appointments/` e recursos auxiliares.

## Testes relacionados
`test_agenda_complete.py`, testes de telemedicina e performance.

## Status de implementação
Implementado.

---

# UC-AGE-002 — Alterar estado da consulta

## Fluxo principal
Usuário autorizado confirma, conclui, registra falta, cancela ou remarca conforme actions do ViewSet e regras do domínio.

## Pós-condições
Status e dados de cancelamento/remarcação são persistidos; integrações financeiras podem reagir.

## Status de implementação
Implementado.

---

# UC-AGE-003 — Acessar telemedicina

## Fluxo principal
1. Participante recebe token/URL por canal autorizado.
2. Acessa rota pública com role e UUID.
3. Backend valida token e sala.
4. Acesso é concedido apenas durante condições previstas.

## Limitação
A presença de models/rotas não comprova infraestrutura audiovisual completa em produção.

## Status de implementação
Parcialmente implementado operacionalmente.

[Voltar](README.md)
