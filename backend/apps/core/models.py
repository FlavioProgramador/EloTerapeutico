"""Modelos técnicos do app compartilhado.

O modelo abaixo é não gerenciado e existe somente para fornecer uma permissão
Django explícita. Nenhuma tabela adicional é criada no banco.
"""

from django.db import models


class SQLExplorerPermission(models.Model):
    """Âncora de ContentType para a permissão administrativa sensível."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("use_sql_explorer", "Pode utilizar o SQL Explorer administrativo"),
        )
        verbose_name = "Acesso ao SQL Explorer"
        verbose_name_plural = "Acessos ao SQL Explorer"
