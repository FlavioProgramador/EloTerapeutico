"""Permissões específicas de documentos clínicos."""

from rest_framework.permissions import IsAuthenticated


class IsClinicalDocumentUser(IsAuthenticated):
    """Impede que secretárias acessem conteúdo clínico documental."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_secretary
