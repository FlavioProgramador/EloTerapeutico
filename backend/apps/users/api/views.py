"""Views de autenticação, sessões, perfil e horários de atendimento."""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import connection
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from ..models import AuthSession, PracticeSettings, User, WorkingHours
from ..services.sessions import (
    SESSION_CLAIM,
    active_sessions_for_user,
    issue_token_pair,
    revoke_all_user_sessions,
    revoke_refresh_token,
    revoke_user_session,
)
from .serializers import (
    AuthSessionSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PracticeSettingsSerializer,
    RegisterSerializer,
    SafeTokenRefreshSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    WorkingHoursSerializer,
)

logger = logging.getLogger(__name__)


def _refresh_token_for_user(raw_token: str, user) -> RefreshToken:
    """Valida o refresh token e confirma que pertence ao usuário autenticado."""

    token = RefreshToken(raw_token)
    claim_name = settings.SIMPLE_JWT.get("USER_ID_CLAIM", "user_id")
    token_user_id = token.payload.get(claim_name)
    if token_user_id is None or str(token_user_id) != str(user.pk):
        raise TokenError("Refresh token não pertence ao usuário autenticado.")
    return token


def _current_session_id(request):
    token = getattr(request, "auth", None)
    if token is None:
        return None
    try:
        return token.get(SESSION_CLAIM)
    except AttributeError:
        return None


@extend_schema(tags=["auth"])
@method_decorator(ratelimit(key="ip", rate="10/m", block=True, method="POST"), name="post")
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = issue_token_pair(user=user, request=request)
        return Response(
            {
                "message": "Cadastro realizado com sucesso.",
                "tokens": tokens,
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["auth"])
@method_decorator(ratelimit(key="ip", rate="5/m", block=True, method="POST"), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_200_OK)


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
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
            refresh = _refresh_token_for_user(refresh_token, request.user)
            revoke_refresh_token(
                refresh=refresh,
                user=request.user,
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


@extend_schema(tags=["auth"])
class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        revoked_count = revoke_all_user_sessions(
            user=request.user,
            reason="logout_all",
        )
        return Response(
            {
                "message": "Todas as sessões foram encerradas.",
                "revoked_sessions": revoked_count,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["auth"], responses=AuthSessionSerializer(many=True))
class AuthSessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = active_sessions_for_user(user=request.user)
        serializer = AuthSessionSerializer(
            sessions,
            many=True,
            context={"current_session_id": _current_session_id(request)},
        )
        return Response(serializer.data)


@extend_schema(tags=["auth"])
class AuthSessionRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        try:
            session = revoke_user_session(
                user=request.user,
                public_id=public_id,
            )
        except AuthSession.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Sessão não encontrada.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": "Sessão encerrada com sucesso.",
                "session": str(session.public_id),
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["auth"])
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Senha alterada com sucesso."})


@extend_schema(tags=["users"])
class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserProfileUpdateSerializer
        return UserProfileSerializer




@extend_schema(tags=["users"], responses=PracticeSettingsSerializer)
class PracticeSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PracticeSettingsSerializer

    def get_object(self):
        settings_obj, _ = PracticeSettings.objects.get_or_create(
            user=self.request.user,
            defaults={
                "trade_name": self.request.user.clinic_name,
                "phone": self.request.user.phone,
                "email": self.request.user.email,
                "address": self.request.user.professional_address,
                "timezone": self.request.user.timezone,
            },
        )
        return settings_obj

    def perform_update(self, serializer):
        obj = serializer.save()
        from apps.audit.services.access_logging import log_access
        from apps.audit.models import AuditLog

        log_access(
            self.request,
            AuditLog.Action.UPDATE,
            obj=obj,
            obj_repr=f"users.PracticeSettings#{obj.pk} action=settings_updated",
        )

@extend_schema(tags=["users"])
class WorkingHoursListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkingHours.objects.filter(therapist=self.request.user)


@extend_schema(tags=["users"])
class WorkingHoursDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkingHours.objects.filter(therapist=self.request.user)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            database_status = "ok"
        except Exception:
            database_status = "error"

        return Response(
            {
                "status": "ok" if database_status == "ok" else "degraded",
                "timestamp": timezone.now().isoformat(),
                "services": {"database": database_status},
            }
        )


@extend_schema(tags=["auth"])
@method_decorator(ratelimit(key="ip", rate="3/h", block=True, method="POST"), name="post")
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=True)
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            frontend_url = getattr(
                settings,
                "FRONTEND_URL",
                "http://localhost:3000",
            )
            reset_url = f"{frontend_url}/forgot-password/reset?token={token}&uid={uidb64}"
            subject = "Redefinição de senha — Elo Terapêutico"
            message = (
                f"Olá, {user.full_name}.\n\n"
                "Você solicitou a redefinição de senha para "
                "sua conta no Elo Terapêutico.\n"
                "Para prosseguir, acesse o link abaixo:\n"
                f"{reset_url}\n\n"
                "Este link é válido por tempo limitado.\n"
                "Caso não tenha solicitado, desconsidere este e-mail.\n"
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception as exc:
                logger.error(
                    "password_reset_email_failed",
                    extra={"exception_type": exc.__class__.__name__},
                )
        except User.DoesNotExist:
            pass

        return Response(
            {"message": "Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha."},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["auth"])
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Senha redefinida com sucesso."},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["auth"])
class SafeTokenRefreshView(TokenRefreshView):
    authentication_classes = []
    serializer_class = SafeTokenRefreshSerializer


__all__ = [
    "AuthSessionListView",
    "AuthSessionRevokeView",
    "ChangePasswordView",
    "HealthCheckView",
    "LoginView",
    "LogoutAllView",
    "LogoutView",
    "MeView",
    "PasswordResetConfirmView",
    "PasswordResetRequestView",
    "PracticeSettingsView",
    "RegisterView",
    "SafeTokenRefreshView",
    "WorkingHoursDetailView",
    "WorkingHoursListCreateView",
]
