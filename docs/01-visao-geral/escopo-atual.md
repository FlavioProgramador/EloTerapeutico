# Escopo atual

## Fronteira do sistema

O backend expõe a API sob `/api/v1/`, além de OpenAPI, health check e administração Django. O frontend consome a API por `NEXT_PUBLIC_API_URL` e organiza páginas públicas, autenticação, checkout e dashboard.

## Domínios instalados

`core`, `infrastructure`, `users`, `patients`, `records`, `agenda`, `financeiro`, `documents`, `reports`, `forms`, `billing` e `audit`.

Implementação relacionada: `backend/config/settings/base.py`.

## Isolamento atual

A propriedade de registros é normalmente representada por chaves estrangeiras para `User`, especialmente o terapeuta. Selectors, querysets e permissões filtram dados acessíveis ao usuário.

**Não existe, na revisão analisada, uma entidade explícita de organização, clínica ou tenant.** Consequentemente:

- o sistema não deve ser divulgado como multi-clínica pronto;
- administradores e secretárias exigem revisão cuidadosa de escopo;
- uma futura arquitetura multi-tenant precisa definir associação de usuários, pacientes, billing, auditoria e storage ao tenant.

## Fora do escopo desta documentação

- aconselhamento jurídico definitivo;
- validação de conformidade profissional para todas as especialidades;
- garantias de disponibilidade ou segurança sem o ambiente de produção;
- descrição de funções planejadas que não possuam implementação verificável.

[Voltar](README.md)
