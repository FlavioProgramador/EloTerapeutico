from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.billing.services.entitlements import get_entitlement
from apps.users.models import AuthSession
from apps.users.services.sessions import SESSION_CLAIM


class SubscriptionRequired(APIException):
    status_code = 402
    default_detail = (
        "É necessário possuir uma assinatura ativa ou um teste gratuito válido."
    )
    default_code = "subscription_required"

    def __init__(self, *, code: str, message: str):
        self.default_code = code.lower()
        super().__init__(detail=message, code=self.default_code)


class SubscriptionJWTAuthentication(JWTAuthentication):
    """Autentica JWT, valida a sessão revogável e aplica entitlement."""

    PUBLIC_AUTH_PATHS = {
        "/api/v1/auth/register/",
        "/api/v1/auth/login/",
        "/api/v1/auth/logout/",
        "/api/v1/auth/logout-all/",
        "/api/v1/auth/me/",
        "/api/v1/auth/onboarding/",
        "/api/v1/auth/sessions/",
        "/api/v1/auth/token/refresh/",
        "/api/v1/auth/password/change/",
        "/api/v1/auth/password/reset/",
        "/api/v1/auth/password/reset/confirm/",
    }
    PUBLIC_AUTH_PREFIXES = ("/api/v1/auth/sessions/",)
    ACCESS_MANAGEMENT_PREFIXES = (
        "/api/v1/billing/",
        "/api/schema/",
        "/api/docs/",
    )

    def _validate_auth_session(self, *, user, token) -> None:
        session_id = token.get(SESSION_CLAIM)
        if not session_id:
            if getattr(settings, "AUTH_REQUIRE_SESSION_CLAIM", True):
                raise AuthenticationFailed("Sessão inválida ou expirada.")
            return

        session_exists = AuthSession.objects.filter(
            public_id=session_id,
            user=user,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).exists()
        if not session_exists:
            raise AuthenticationFailed("Sessão inválida ou expirada.")

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is None:
            return None

        user, token = authenticated
        self._validate_auth_session(user=user, token=token)

        if not getattr(settings, "BILLING_REQUIRE_SUBSCRIPTION", True):
            return user, token

        path = request.path
        if (
            path in self.PUBLIC_AUTH_PATHS
            or path.startswith(self.PUBLIC_AUTH_PREFIXES)
            or path.startswith(self.ACCESS_MANAGEMENT_PREFIXES)
        ):
            return user, token

        entitlement = get_entitlement(user)
        if not entitlement.allowed:
            raise SubscriptionRequired(
                code=entitlement.code,
                message=entitlement.message,
            )
        return user, token
