# Casos de uso — Documentos e formulários

# UC-DOC-001 — Gerar documento

## Objetivo
Gerar PDF rastreável a partir de template e paciente.

## Atores
Profissional autorizado.

## Pré-condições
Template e paciente acessíveis; dados profissionais configurados.

## Fluxo principal
1. Usuário escolhe template e paciente.
2. Backend resolve placeholders permitidos.
3. Cria snapshot criptografado do template/contexto.
4. Gera número único por owner.
5. Renderiza PDF, calcula hash e marca concluído.
6. Download exige autorização.

## Fluxos alternativos
Template da biblioteca é importado como cópia privada antes do uso quando exigido.

## Exceções
Placeholder inválido, geração falha ou idempotency key repetida.

## Regras de segurança
Sanitização, storage privado, autorização por owner/paciente e não exposição de contexto.

## Status de implementação
Implementado.

---

# UC-FOR-001 — Criar formulário

## Fluxo principal
1. Profissional cria formulário vazio ou a partir de template.
2. Adiciona campos ordenados com tipo e configuração.
3. Backend valida e salva como ativo.
4. Formulário pode ser duplicado ou arquivado.

## Status de implementação
Implementado.

---

# UC-FOR-002 — Preencher e enviar submissão

## Fluxo principal
1. Submissão em rascunho é associada a formulário e opcionalmente paciente/consulta.
2. Respostas são salvas por campo.
3. Ao enviar, status vira `submitted`, com usuário e horário.
4. Revisão posterior usa transição própria quando disponível.

## Exceções
Campo obrigatório/tipo inválido ou acesso fora do owner.

## Dados envolvidos
Respostas potencialmente clínicas; aplicar minimização e retenção.

## Status de implementação
Implementado.

[Voltar](README.md)
