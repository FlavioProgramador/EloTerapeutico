# Módulo de usuários

**Status: implementado.**

## Finalidade

Representar profissionais, secretárias e administradores, armazenar perfil e preferências básicas de agenda.

## Modelo de dados

### User

- identificação: `email`, `full_name`;
- papel: `therapist`, `secretary` ou `admin`;
- perfil: especialidade, CRP, bio, telefone e avatar;
- padrões: duração e valor de sessão;
- conta: ativo, staff, data de cadastro e último login;
- segurança: falhas e bloqueio temporário.

### WorkingHours

Associa um usuário a um dia da semana, início, fim e ativação. Há unicidade por terapeuta e dia.

## API

| Método | Rota | Uso |
| --- | --- | --- |
| GET/PATCH/PUT | `/api/v1/auth/me/` | Consultar/editar o próprio perfil |
| GET/POST | `/api/v1/auth/working-hours/` | Listar/criar horários próprios |
| GET/PATCH/PUT/DELETE | `/api/v1/auth/working-hours/{id}/` | Gerenciar horário próprio |

`email`, `role`, datas e identificador são somente leitura no perfil.

## Permissões

Todos os endpoints exigem autenticação. O queryset de horários é filtrado pelo usuário da requisição.

O papel administrativo não confere automaticamente permissão explícita para evoluções confidenciais. Permissões clínicas especiais usam codenames do app `records`.

## Frontend

Configurações e contexto de autenticação usam o perfil retornado pela API. O cookie `auth_role` auxilia o middleware, mas não é fonte confiável para autorização.

## Segurança

- validação de telefone e CRP;
- senha nunca é serializada;
- role não é alterável pelo endpoint de perfil;
- avatares exigem storage e política de upload apropriados.

## Limitações

- não há associação explícita a clínica/organização;
- não há fluxo documentado de convite de equipe;
- permissões Django e roles coexistem e devem ser auditadas;
- desativação e desligamento de profissionais exigem procedimento para pacientes e registros protegidos.

[Voltar aos módulos](../README.md)
