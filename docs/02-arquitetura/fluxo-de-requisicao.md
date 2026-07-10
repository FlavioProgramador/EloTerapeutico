# Fluxo de requisição

```mermaid
sequenceDiagram
    actor U as Usuário
    participant F as Next.js
    participant I as Interceptor Axios
    participant A as API Django
    participant P as Permission/Selector
    participant B as Banco
    participant L as Auditoria

    U->>F: Executa ação
    F->>I: Monta requisição
    I->>A: Bearer access token
    A->>A: Autentica JWT
    A->>P: Valida permissão e escopo
    P->>B: Consulta ou persiste
    B-->>P: Resultado
    opt recurso sensível
        A->>L: Registra ação técnica
        L->>B: Cria AuditLog
    end
    A-->>I: JSON ou erro padronizado
    I-->>F: Atualiza cache/estado
    F-->>U: Loading, sucesso, vazio ou erro
```

## Refresh

Quando a API retorna `401`, o interceptor coordena uma única chamada a `/auth/token/refresh/`, enfileira requisições simultâneas e repete as chamadas após receber o novo access token. Se o refresh falha, limpa os cookies e redireciona para login.

## Responsabilidades

- frontend: experiência, validação preliminar e cache;
- backend: validação definitiva, autorização, integridade e auditoria;
- banco: constraints e transações;
- storage: persistência privada dos arquivos;
- infraestrutura: TLS, disponibilidade, backup e observabilidade.

[Voltar](README.md)
