# mypy: ignore-errors
"""Paginação compartilhada pela API REST."""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """Padroniza paginação por número de página em todos os endpoints.

    A resposta agrupa os metadados em ``pagination`` e mantém os itens em
    ``results``. O cliente pode alterar ``page_size`` até o limite de 100
    registros por requisição.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        """Monta a resposta paginada usada pelo frontend.

        Args:
            data: Coleção já serializada correspondente à página atual.

        Returns:
            Resposta HTTP contendo contagem, páginas, links de navegação e
            resultados serializados.
        """
        return Response(
            {
                "pagination": {
                    "count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        """Descreve no OpenAPI o envelope de paginação customizado.

        Args:
            schema: Schema OpenAPI dos itens presentes em ``results``.

        Returns:
            Objeto OpenAPI com metadados de paginação e lista de resultados.
        """
        return {
            "type": "object",
            "properties": {
                "pagination": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "current_page": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                    },
                },
                "results": schema,
            },
        }
