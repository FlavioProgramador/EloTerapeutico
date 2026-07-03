---
name: django-expert
description: Orientações especializadas para desenvolvimento backend com Django e Django REST Framework.
---

# Django Expert

Use esta skill em alterações de models, ORM, migrations, serializers, views, APIs, autenticação, permissões, testes, desempenho e implantação.

## Fluxo obrigatório

1. Leia a estrutura e os padrões existentes antes de alterar código.
2. Confirme as versões de Django e Django REST Framework.
3. Preserve migrations aplicadas e contratos públicos da API.
4. Mantenha views finas; mova regras de escrita complexas para services e consultas reutilizáveis para selectors ou managers.
5. Combine permissions por objeto com isolamento no queryset.
6. Use `select_related` e `prefetch_related` para evitar N+1.
7. Prefira constraints e índices de banco para regras persistentes.
8. Cubra caminhos positivos, negativos e não autorizados com testes.
9. Execute checks do Django, verificação de migrations e a suíte configurada.

## Regras de qualidade

- Siga PEP 8 e as convenções do Django.
- Evite imports circulares e módulos genéricos sem responsabilidade clara.
- Não edite migrations que possam ter sido aplicadas.
- Não permita que regras de domínio dependam de objetos HTTP.
- Preserve o isolamento entre usuários, terapeutas e pacientes.

## Origem

Baseada na skill MIT `django-expert` do repositório `vintasoftware/django-ai-plugins`.
