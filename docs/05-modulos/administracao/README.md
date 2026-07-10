# Módulo de administração

**Status: implementado.**

## Finalidade

Fornecer backoffice interno via Django Admin, estilizado com Django Unfold, para suporte e gestão autorizada.

## Áreas configuradas

- dashboard e SQL Explorer;
- pacientes, evoluções e anamneses;
- consultas, salas e telemedicina;
- transações financeiras;
- planos, assinaturas, pagamentos e webhooks;
- usuários;
- auditoria;
- modelos de documentos;
- formulários.

## Permissões

O acesso exige `is_staff` e permissões Django. Role `admin` do domínio e `is_staff` são conceitos distintos. Superusuário não deve ser usado no trabalho cotidiano.

Conteúdo clínico confidencial possui regras adicionais e não deve ficar disponível apenas porque alguém é administrador global. O admin de records possui testes específicos de confidencialidade.

## SQL Explorer

Rotas internas `/admin/sql-explorer/` e `/admin/sql-schema/` ampliam risco. Devem ser restritas, auditadas e preferencialmente desabilitadas ou limitadas em produção conforme necessidade.

## Segurança operacional

- MFA no provedor/SSO ou camada de acesso, quando disponível;
- rede restrita ou zero trust;
- sessões curtas e revogação ao desligar usuário;
- menor privilégio;
- proibição de exportar dados para dispositivos não autorizados;
- revisão periódica de staff, grupos e permissões.

## Limitações

O Django Admin é backoffice, não um CRM multi-tenant. A interface não substitui processo de suporte, segregação de funções e revisão de acesso.

[Voltar aos módulos](../README.md)
