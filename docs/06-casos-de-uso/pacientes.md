# Casos de uso — Pacientes

# UC-PAC-001 — Cadastrar paciente

## Objetivo
Criar cadastro administrativo vinculado a profissional responsável.

## Atores
Terapeuta, administrador ou secretária autorizada.

## Pré-condições
Usuário autenticado; terapeuta responsável acessível.

## Permissões necessárias
`PatientPermission` e validações do serializer.

## Gatilho
Envio do formulário de paciente.

## Fluxo principal
1. Interface coleta dados mínimos e responsáveis quando necessários.
2. API normaliza e valida CPF, telefones, status e relacionamentos.
3. Paciente é criado com status e terapeuta.
4. Resposta retorna representação autorizada.

## Fluxos alternativos
### A1 — Importação em lote
Terapeuta envia CSV; API gera preview, aponta duplicidades/erros e só importa após `confirm=true`.

## Exceções
CPF inválido/duplicado, campos inconsistentes, CSV acima de 2 MB ou 500 linhas.

## Pós-condições
Paciente disponível nos querysets acessíveis e em módulos relacionados.

## Dados envolvidos
Dados cadastrais, contatos, responsáveis, convênio e consentimento administrativo.

## Eventos de auditoria
Importação confirmada registra CREATE; outras views sensíveis devem usar mixin/log explícito.

## Regras de segurança
Minimização; isolamento por selector; sem dados reais em testes.

## Endpoints relacionados
`POST /api/v1/patients/`, `POST /patients/import-csv/`.

## Componentes relacionados
Feature `patients`, formulário e serviço de API.

## Testes relacionados
`test_patients.py`, `test_patient_listing_refactor.py`.

## Status de implementação
Implementado.

---

# UC-PAC-002 — Consultar workspace do paciente

## Fluxo principal
1. Usuário acessa paciente permitido.
2. API carrega cadastro, próxima sessão e indicadores.
3. Apenas terapeuta/admin recebe evolução e documentos clínicos permitidos.
4. A visualização é auditada.

## Fluxos alternativos
Secretária recebe `can_access_records=false` e não recebe conteúdo clínico.

## Status de implementação
Implementado.

---

# UC-PAC-003 — Desativar ou restaurar paciente

## Fluxo principal
1. Usuário autorizado aciona `deactivate` ou `restore`.
2. Serviço de lifecycle valida a transição.
3. Estado e arquivamento são atualizados.

## Exceções
Transição inválida retorna 400 sem alteração.

## Status de implementação
Implementado.

[Voltar](README.md)
