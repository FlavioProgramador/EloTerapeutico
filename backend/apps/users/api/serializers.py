"""Serializers de autenticação, perfil, sessões e horários de atendimento."""

import secrets

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from ..models import AuthSession, PracticeSettings, User, WorkingHours
from ..services.sessions import (
    issue_token_pair,
    revoke_all_user_sessions,
    rotate_refresh_token,
)

_INVALID_CREDENTIALS_MESSAGE = "E-mail ou senha incorretos."
_INVALID_TOKEN_MESSAGE = "Token inválido ou expirado."  # nosec B105 -- mensagem pública, não credencial


def _validate_password_strength(password: str, *, user=None, field: str = "password") -> None:
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({field: exc.messages}) from exc


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "password",
            "password_confirm",
            "crp_number",
            "specialty",
            "phone",
        ]

    def validate(self, attrs):
        password_confirm = attrs.pop("password_confirm")
        if attrs["password"] != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "As senhas não conferem."}  # nosec B105 -- mensagem de validação
            )

        candidate_user = User(
            email=attrs.get("email", ""),
            full_name=attrs.get("full_name", ""),
        )
        _validate_password_strength(attrs["password"], user=candidate_user)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            User().set_password(password)
            raise serializers.ValidationError(_INVALID_CREDENTIALS_MESSAGE)

        password_is_valid = user.check_password(password)
        if user.is_locked():
            raise serializers.ValidationError(_INVALID_CREDENTIALS_MESSAGE)

        if not password_is_valid:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lock_account(minutes=30)
            else:
                user.save(update_fields=["failed_login_attempts"])
            raise serializers.ValidationError(_INVALID_CREDENTIALS_MESSAGE)

        if not user.is_active:
            raise serializers.ValidationError(_INVALID_CREDENTIALS_MESSAGE)

        user.reset_login_attempts()
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        tokens = issue_token_pair(
            user=user,
            request=self.context.get("request"),
        )
        return {
            **tokens,
            "user": UserProfileSerializer(user).data,
        }


class ChangePasswordSerializer(serializers.Serializer):
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
            raise serializers.ValidationError(
                {"new_password_confirm": "As novas senhas não conferem."}  # nosec B105 -- mensagem de validação
            )
        _validate_password_strength(
            attrs["new_password"],
            user=self.context["request"].user,
            field="new_password",
        )
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        revoke_all_user_sessions(user=user, reason="password_changed")
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "display_name",
            "profession",
            "role",
            "specialty",
            "crp_number",
            "bio",
            "phone",
            "avatar",
            "clinic_name",
            "professional_address",
            "default_session_duration",
            "default_session_value",
            "default_modality",
            "timezone",
            "language",
            "date_format",
            "time_format",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login", "role"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "full_name",
            "display_name",
            "profession",
            "specialty",
            "crp_number",
            "bio",
            "phone",
            "avatar",
            "clinic_name",
            "professional_address",
            "default_session_duration",
            "default_session_value",
            "default_modality",
            "timezone",
            "language",
            "date_format",
            "time_format",
        ]

    def validate_default_session_duration(self, value):
        if value < 15 or value > 240:
            raise serializers.ValidationError("A duração deve estar entre 15 e 240 minutos.")
        return value


class PracticeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeSettings
        fields = [
            "trade_name",
            "document",
            "phone",
            "email",
            "address",
            "timezone",
            "currency",
            "appointment_interval_minutes",
            "minimum_booking_notice_hours",
            "cancellation_notice_hours",
            "allow_overbooking",
            "consider_holidays",
            "reminders_enabled",
            "reminder_minutes",
            "internal_communications_enabled",
            "message_preview_enabled",
            "auto_mark_read",
            "mentions_enabled",
            "notify_mentions",
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "communication_policy",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate(self, attrs):
        enabled = attrs.get("quiet_hours_enabled", getattr(self.instance, "quiet_hours_enabled", False))
        start = attrs.get("quiet_hours_start", getattr(self.instance, "quiet_hours_start", None))
        end = attrs.get("quiet_hours_end", getattr(self.instance, "quiet_hours_end", None))
        if enabled and (start is None or end is None):
            raise serializers.ValidationError({"quiet_hours_start": "Informe o início e o fim do horário de silêncio."})
        return attrs

    def validate_appointment_interval_minutes(self, value):
        if value > 180:
            raise serializers.ValidationError("O intervalo não pode ultrapassar 180 minutos.")
        return value

    def validate_reminder_minutes(self, value):
        if value > 43200:
            raise serializers.ValidationError("A antecedência não pode ultrapassar 30 dias.")
        return value


class AuthSessionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = AuthSession
        fields = [
            "public_id",
            "user_agent",
            "created_at",
            "last_seen_at",
            "expires_at",
            "is_current",
        ]
        read_only_fields = fields

    def get_is_current(self, obj: AuthSession) -> bool:
        current_session_id = self.context.get("current_session_id")
        return bool(current_session_id and str(obj.public_id) == str(current_session_id))


class WorkingHoursSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(
        source="get_weekday_display",
        read_only=True,
    )

    class Meta:
        model = WorkingHours
        fields = [
            "id",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_active",
        ]

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("O horário de início deve ser anterior ao horário de fim.")
        return attrs

    def create(self, validated_data):
        validated_data["therapist"] = self.context["request"].user
        return super().create(validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "As senhas não conferem."}  # nosec B105 -- mensagem de validação
            )

        try:
            uid = force_str(urlsafe_base64_decode(attrs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {"token": "O link de redefinição é inválido ou expirou."}  # nosec B105 -- mensagem pública
            )

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": "O link de redefinição é inválido ou expirou."}  # nosec B105 -- mensagem pública
            )

        _validate_password_strength(attrs["new_password"], user=user, field="new_password")
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        revoke_all_user_sessions(user=user, reason="password_reset")
        return user


class SafeTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs["refresh"])
        except TokenError as exc:
            raise InvalidToken(_INVALID_TOKEN_MESSAGE) from exc

        token_hash = refresh.get("hash_password")
        user_id = refresh.get("user_id")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise InvalidToken(_INVALID_TOKEN_MESSAGE) from exc

        current_hash = get_md5_hash_password(user.password)
        if (
            not user.is_active
            or not token_hash
            or not secrets.compare_digest(str(token_hash), str(current_hash))
        ):
            raise InvalidToken(_INVALID_TOKEN_MESSAGE)

        try:
            return rotate_refresh_token(
                refresh=refresh,
                user=user,
                request=self.context.get("request"),
            )
        except TokenError as exc:
            raise InvalidToken(_INVALID_TOKEN_MESSAGE) from exc


__all__ = [
    "AuthSessionSerializer",
    "ChangePasswordSerializer",
    "LoginSerializer",
    "PasswordResetConfirmSerializer",
    "PasswordResetRequestSerializer",
    "PracticeSettingsSerializer",
    "RegisterSerializer",
    "SafeTokenRefreshSerializer",
    "UserProfileSerializer",
    "UserProfileUpdateSerializer",
    "WorkingHoursSerializer",
]
