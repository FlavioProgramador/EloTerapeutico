# 05 — Módulos

Cada página reúne finalidade, situação, entidades, regras, API, interface, permissões, segurança, testes e limitações. Módulos pequenos foram consolidados em um único documento para evitar arquivos vazios ou repetitivos.

| Módulo | Documento | Situação |
| --- | --- | --- |
| Autenticação | [autenticacao](autenticacao/README.md) | ✅ |
| Usuários | [usuarios](usuarios/README.md) | ✅ |
| Dashboard | [dashboard](dashboard/README.md) | 🟡 |
| Pacientes | [pacientes](pacientes/README.md) | ✅ |
| Prontuário | [prontuario](prontuario/README.md) | ✅ |
| Agenda | [agenda](agenda/README.md) | ✅ |
| Telemedicina | [telemedicina](telemedicina/README.md) | ⚠️ integração e staging |
| Financeiro | [financeiro](financeiro/README.md) | ✅ |
| Documentos | [documentos](documentos/README.md) | ✅ |
| Formulários | [formularios](formularios/README.md) | ✅ |
| Relatórios | [relatorios](relatorios/README.md) | 🟡 |
| Billing/assinatura | [billing](billing/README.md) | ✅ |
| Auditoria | [auditoria](auditoria/README.md) | ✅ |
| Administração | [administracao](administracao/README.md) | ✅ |
| Configurações | [configuracoes](configuracoes.md) | ✅ |
| Notificações | [notificacoes](notificacoes.md) | ✅ |

A telemedicina possui implementação funcional, mas depende de credenciais LiveKit, HTTPS/WSS, webhook e validação em staging antes de uso real.

[Voltar ao índice](../README.md)
