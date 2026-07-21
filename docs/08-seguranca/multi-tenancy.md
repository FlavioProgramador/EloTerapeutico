# Segurança multi-tenant

## Objetivo

Impedir que um usuário autenticado de uma organização visualize, altere, exporte ou processe dados pertencentes a outra organização.

## Princípios

1. O tenant é explícito e persistido em cada recurso operacional.
2. O frontend não é fonte de autorização.
3. `X-Organization-ID` é apenas uma preferência de contexto; o backend valida a membership em todas as requisições.
4. Selectors recebem `organization` explicitamente.
5. Services definem o tenant a partir do contexto autenticado, nunca de um campo livre do payload.
6. Tasks, relatórios, exportações e arquivos carregam `organization_id`.
7. Respostas de acesso cruzado não revelam a existência do recurso.

## Resolução do tenant

O autenticador tenant-aware executa após a validação do JWT e da sessão revogável:

```text
JWT válido
  -> sessão ativa
    -> X-Organization-ID válido
      -> membership ativa
        -> organization ativa
          -> request.organization
          -> request.organization_membership
```

Organizações suspensas ou arquivadas não fornecem contexto operacional.

## Papéis e capacidades

Permissões são verificadas por capacidades centralizadas. Não utilizar verificações espalhadas como `if user.role == "admin"`.

O papel global legado do usuário não substitui a membership. Um usuário pode ser terapeuta em uma organização e administrador em outra.

## Relações cruzadas

Services e models validam, entre outros:

- paciente e consulta na mesma organização;
- consulta, sala, pacote e recorrência no mesmo tenant;
- evolução, anamnese, documento e exportação ligados ao paciente da organização;
- profissional com membership ativa;
- arquivo e relatório filtrados pelo tenant;
- cache e idempotência incluindo organização.

## Logs

Não registrar:

- conteúdo clínico;
- token de convite;
- senha ou JWT;
- CPF completo;
- documentos ou payload bruto.

A auditoria persiste `organization` separadamente e aceita recursos UUID sem converter identificadores para inteiro.

## Teste obrigatório

Todo novo recurso tenant-owned deve possuir teste com duas organizações:

1. criar dado no tenant A;
2. autenticar usuário do tenant B;
3. tentar listar, detalhar, alterar, excluir e exportar;
4. confirmar resposta segura e ausência do dado.
