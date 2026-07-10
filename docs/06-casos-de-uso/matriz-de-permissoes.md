# Matriz de permissões, dados e riscos

| Ator | Módulo/caso | Permissão principal | Dados acessados | Risco | Status |
| --- | --- | --- | --- | --- | --- |
| Público | Cadastro/login/reset | `AllowAny` + rate limit | identidade e credencial | enumeração/brute force | Implementado |
| Terapeuta | Gerir paciente | autenticação + selector | cadastro e responsáveis | acesso cruzado | Implementado |
| Secretária | Cadastrar/consultar paciente | métodos limitados | dados administrativos | escalada para clínico | Implementado |
| Terapeuta | Criar evolução | acesso ao paciente | dado clínico sensível | vazamento/alteração | Implementado |
| Autor/permissão explícita | Ver evolução confidencial | codename records | conteúdo clínico | acesso privilegiado | Implementado |
| Terapeuta | Exportar prontuário | autorização e auditoria | conjunto clínico | exfiltração | Implementado |
| Worker | Processar exportação | acesso interno ao banco/storage | prontuário autorizado | job indevido | Implementado |
| Terapeuta/secretária autorizada | Agenda | queryset por acesso | horários e paciente | conflito/vazamento | Implementado |
| Terapeuta | Financeiro | owner | valores e pagamentos | exposição financeira | Implementado |
| Terapeuta | Gerar documento | owner + paciente | dados pessoais/clínicos | documento incorreto | Implementado |
| Usuário autenticado | Checkout | própria conta | cobrança/CPF no trânsito | fraude/vazamento | Implementado |
| Asaas | Webhook | token compartilhado | evento de pagamento | falsificação/replay | Implementado |
| Staff | Admin | Django permissions | múltiplos domínios | excesso de privilégio | Implementado |
| Clínica/tenant | Isolamento institucional | inexistente | todos | mistura entre clínicas | Não implementado |

## Observações

- permissões de interface não substituem backend;
- superusuário não recebe automaticamente acesso confidencial na função específica de evoluções;
- acesso ao paciente não implica acesso irrestrito ao prontuário;
- permissões precisam ser retestadas quando houver associação a clínica/equipe.

[Voltar](README.md)
