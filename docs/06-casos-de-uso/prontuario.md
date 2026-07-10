# Casos de uso — Prontuário

# UC-REC-001 — Registrar evolução clínica

## Objetivo
Registrar informações da sessão com integridade, confidencialidade e vínculo opcional à agenda.

## Atores
Terapeuta autorizado.

## Pré-condições
Paciente acessível; data não futura; consulta elegível quando vinculada.

## Permissões necessárias
Acesso ao paciente e ao domínio records.

## Gatilho
Salvamento do editor de evolução.

## Fluxo principal
1. Terapeuta seleciona paciente/consulta e informa data e conteúdo.
2. Backend sanitiza Markdown e valida limites.
3. Datas retroativas são avaliadas.
4. Conteúdo é criptografado na persistência.
5. Evolução permanece editável por até 48 horas, salvo finalização.
6. Operação é auditada quando a view usa o fluxo seguro.

## Fluxos alternativos
### A1 — Evolução confidencial
Acesso posterior é limitado ao autor ou permissão explícita.

### A2 — Anexo
Arquivo passa por limite, extensão, MIME e magic bytes antes de ser salvo.

## Exceções
Data futura, retroatividade não autorizada, HTML perigoso, limite excedido ou arquivo inválido.

## Pós-condições
Evolução e versões relacionadas ficam disponíveis ao conjunto autorizado.

## Dados envolvidos
Conteúdo clínico, CID opcional, data, autor, confidencialidade, anexos.

## Eventos de auditoria
CREATE/UPDATE/VIEW conforme endpoint.

## Regras de segurança
Criptografia em repouso no campo; autorização no backend; storage privado; não registrar conteúdo.

## Endpoints relacionados
`/records/patients/{id}/clinical-evolutions/` e `/records/clinical-evolutions/{id}/`.

## Componentes relacionados
Editor de evolução e abas de records.

## Testes relacionados
Testes de modal, segurança, refatoração clínica e confidencialidade.

## Status de implementação
Implementado.

---

# UC-REC-002 — Finalizar e retificar evolução

## Fluxo principal
1. Autor finaliza evolução.
2. Backend marca bloqueio e horário.
3. Conteúdo original não pode mais ser editado.
4. Retificação é criada como `EvolutionAddendum` com motivo, conteúdo e autor.

## Exceções
Tentativa de editar evolução bloqueada é recusada.

## Status de implementação
Implementado.

---

# UC-REC-003 — Exportar prontuário

## Objetivo
Gerar PDF sem incluir conteúdo confidencial não autorizado.

## Fluxo principal
1. Usuário solicita exportação.
2. API cria job `PENDING`.
3. Worker reserva o job em transação.
4. Evoluções são filtradas por confidencialidade.
5. Markdown é renderizado de forma segura.
6. PDF é salvo em storage e job vira `COMPLETED`.
7. Usuário autorizado solicita download.

## Fluxos alternativos
Falha temporária retorna job a `PENDING`; retry manual existe para falhas elegíveis.

## Exceções
Após três tentativas o job fica `FAILED`; download sem autorização é recusado.

## Eventos de auditoria
EXPORT e download conforme views seguras.

## Status de implementação
Implementado; requer worker e storage.

---

# UC-REC-004 — Consultar anamnese e histórico

## Fluxo principal
1. Usuário autorizado abre anamnese clínica.
2. API retorna perfil e dados atuais.
3. Atualizações criam/expõem versões conforme fluxo.

## Status de implementação
Implementado.

[Voltar](README.md)
