"""
apps/users/views.py
Views de autenticação, perfil e horários de atendimento.
"""

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, WorkingHours
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    WorkingHoursSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Autenticação
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["auth"])
class RegisterView(generics.CreateAPIView):
    """Cadastro de novo terapeuta no sistema."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Cadastro realizado com sucesso.",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=["auth"])
class LoginView(APIView):
    """Autenticação do usuário e retorno de tokens JWT."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    """Invalida o refresh token (blacklist) encerrando a sessão."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
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
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logout realizado com sucesso."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Token inválido ou já expirado.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["auth"])
class ChangePasswordView(APIView):
    """Altera a senha do usuário autenticado."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Senha alterada com sucesso."})


# ─────────────────────────────────────────────────────────────────────────────
# Perfil do Terapeuta
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["users"])
class MeView(generics.RetrieveUpdateAPIView):
    """Retorna e permite atualização do perfil do usuário autenticado."""
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserProfileUpdateSerializer
        return UserProfileSerializer


# ─────────────────────────────────────────────────────────────────────────────
# Horários de Atendimento
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["users"])
class WorkingHoursListCreateView(generics.ListCreateAPIView):
    """Lista e cria horários de atendimento do terapeuta autenticado."""
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkingHours.objects.filter(therapist=self.request.user)


@extend_schema(tags=["users"])
class WorkingHoursDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalhe, atualização e remoção de um horário de atendimento."""
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkingHours.objects.filter(therapist=self.request.user)


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

class HealthCheckView(APIView):
    """Endpoint de health check para o Azure App Service monitorar."""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection
        try:
            connection.ensure_connection()
            db_status = "ok"
        except Exception:
            db_status = "error"

        return Response({
            "status": "ok" if db_status == "ok" else "degraded",
            "timestamp": timezone.now().isoformat(),
            "services": {
                "database": db_status,
            },
        })


# ─────────────────────────────────────────────────────────────────────────────
# Redefinição de senha
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["auth"])
class PasswordResetRequestView(APIView):
    """
    Solicita o reset de senha enviando um e-mail com link contendo
    token e uidb64.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.conf import settings

        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=True)
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            frontend_url = getattr(
                settings, "FRONTEND_URL", "http://localhost:3000"
            )
            reset_url = (
                f"{frontend_url}/forgot-password/reset"
                f"?token={token}&uid={uidb64}"
            )

            subject = "Redefinição de senha — Elo Terapêutico"
            message = (
                f"Olá, {user.full_name}.\n\n"
                "Você solicitou a redefinição de senha para "
                "sua conta no Elo Terapêutico.\n"
                f"Para prosseguir, acesse o link abaixo:\n"
                f"{reset_url}\n\n"
                "Este link é válido por tempo limitado.\n"
                "Caso não tenha solicitado, por favor desconsidere "
                "este e-mail.\n"
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                import logging
                logger = logging.getLogger("django")
                logger.error(
                    f"Erro ao enviar e-mail de redefinição: {str(e)}"
                )
        except User.DoesNotExist:
            pass

        # Resposta idêntica para evitar enumeração
        return Response({
            "message": (
                "Se o e-mail estiver cadastrado, você receberá um "
                "link para redefinir sua senha."
            )
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["auth"])
class PasswordResetConfirmView(APIView):
    """Confirma a redefinição de senha usando o token e uidb64 recebidos."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Senha redefinida com sucesso."
        }, status=status.HTTP_200_OK)


