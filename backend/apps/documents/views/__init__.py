"""Views do domínio de documentos."""

from rest_framework.permissions import IsAuthenticated


class IsClinicalDocumentUser(IsAuthenticated):
    """Dados clínicos ficam indisponíveis para o papel de secretária."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_secretary
