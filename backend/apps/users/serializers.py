"""
apps/users/serializers.py
Serializers para autenticação, perfil e horários de atendimento.
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, WorkingHours


# ─────────────────────────────────────────────────────────────────────────────
# Autenticação
# ─────────────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para cadastro de novo terapeuta."""
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "full_name", "password", "password_confirm", "crp_number", "specialty", "phone"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "As senhas não conferem."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer para autenticação e retorno de tokens JWT."""
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Executa dummy password hashing para consumir CPU de forma
            # equivalente
            User().set_password(password)
            raise serializers.ValidationError("E-mail ou senha incorretos.")

        # Verificar bloqueio de conta
        if user.is_locked():
            locked_time = user.locked_until.strftime('%H:%M')
            raise serializers.ValidationError(
                f"Conta bloqueada por tentativas excessivas. "
                f"Tente novamente após {locked_time}."
            )

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lock_account(minutes=30)
            else:
                user.save(update_fields=["failed_login_attempts"])
            raise serializers.ValidationError("E-mail ou senha incorretos.")

        if not user.is_active:
            raise serializers.ValidationError(
                "Conta inativa. Entre em contato com o suporte."
            )

        user.reset_login_attempts()
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserProfileSerializer(user).data,
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para troca de senha autenticado."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "As novas senhas não conferem."})
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ─────────────────────────────────────────────────────────────────────────────
# Perfil
# ─────────────────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer completo para leitura do perfil do terapeuta."""

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "role", "specialty",
            "crp_number", "bio", "phone", "avatar",
            "default_session_duration", "default_session_value",
            "date_joined", "last_login",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login", "role"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização do perfil (campos editáveis)."""

    class Meta:
        model = User
        fields = [
            "full_name", "specialty", "crp_number", "bio",
            "phone", "avatar", "default_session_duration", "default_session_value",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Horários de atendimento
# ─────────────────────────────────────────────────────────────────────────────

class WorkingHoursSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WorkingHours
        fields = ["id", "weekday", "weekday_display", "start_time", "end_time", "is_active"]

    def validate(self, attrs):
        if attrs.get("start_time") and attrs.get("end_time"):
            if attrs["start_time"] >= attrs["end_time"]:
                raise serializers.ValidationError("O horário de início deve ser anterior ao horário de fim.")
        return attrs

    def create(self, validated_data):
        validated_data["therapist"] = self.context["request"].user
        return super().create(validated_data)
