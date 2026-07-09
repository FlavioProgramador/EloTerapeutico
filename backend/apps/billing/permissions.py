from rest_framework.permissions import BasePermission

from apps.billing.services.features import can_use_feature, is_subscription_usable, get_current_subscription


class RequireActiveSubscription(BasePermission):
    message = "Assinatura ativa necessária para acessar este recurso."

    def has_permission(self, request, view):
        if not request.user or request.user.is_anonymous:
            return False
        if getattr(request.user, "is_superuser", False) or getattr(request.user, "is_admin_role", False):
            return True
        return is_subscription_usable(get_current_subscription(request.user))


class RequireFeature(BasePermission):
    message = "Seu plano atual não possui acesso a este recurso."
    feature_key = None

    def has_permission(self, request, view):
        feature_key = getattr(view, "required_feature", None) or self.feature_key
        if not feature_key:
            return True
        return can_use_feature(request.user, feature_key)
