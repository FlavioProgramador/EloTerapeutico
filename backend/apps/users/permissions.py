"""
apps/users/permissions.py
Classes de permissão DRF baseadas no papel (role) do usuário.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsTherapist(IsAuthenticated):
    """Permite acesso apenas a usuários com papel 'therapist'."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_therapist


class IsSecretary(IsAuthenticated):
    """Permite acesso apenas a usuários com papel 'secretary'."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_secretary


class IsAdminRole(IsAuthenticated):
    """Permite acesso apenas a usuários com papel 'admin'."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin_role


class IsTherapistOrAdmin(IsAuthenticated):
    """Permite acesso a terapeutas e administradores."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and (request.user.is_therapist or request.user.is_admin_role)


class IsOwnerOrAdmin(BasePermission):
    """
    Permissão a nível de objeto.
    Garante que somente o terapeuta dono do objeto (ou um admin) possa acessá-lo.
    O objeto deve ter um campo 'therapist' apontando para o User.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_role:
            return True
        therapist = getattr(obj, "therapist", None)
        if therapist is None:
            return False
        return therapist == request.user
