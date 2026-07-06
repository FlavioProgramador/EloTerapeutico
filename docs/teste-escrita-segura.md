# Política segura de pacientes

Este arquivo registra a decisão de produto: a remoção comum de um paciente deve ser tratada como arquivamento lógico, preservando histórico clínico, financeiro, documentos e auditoria.

Regras principais:

- ocultar o paciente da listagem ativa;
- preservar prontuário, documentos, financeiro e logs;
- bloquear novos vínculos operacionais;
- cancelar apenas eventos futuros ainda ativos;
- manter fluxo separado para anonimização definitiva.
