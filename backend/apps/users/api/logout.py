from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.services.sessions import revoke_refresh_token


def _refresh_owner(raw_token: str) -> tuple[RefreshToken, User]:
    refresh = RefreshToken(raw_token)
    user_id = refresh.payload.get("user_id")
    if user_id is None:
        raise TokenError("Refresh token sem usuário.")
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user is None:
        raise TokenError("Usuário do refresh token não está disponível.")
    return refresh, user


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    """Revoga a sessão identificada pelo refresh, sem depender do access token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_token = request.data.get("refresh")
        if not raw_token:
            return Response(
                {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "O campo 'refresh' é obrigatório.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh, user = _refresh_owner(raw_token)
            revoke_refresh_token(
                refresh=refresh,
                user=user,
                reason="logout",
            )
        except TokenError:
            return Response(
                {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Token inválido ou já expirado.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Logout realizado com sucesso."},
            status=status.HTTP_200_OK,
        )


__all__ = ["LogoutView"]
