"""Serializers de autenticação, perfil e horários de atendimento."""

import secrets

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from ..models import User, WorkingHours

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
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
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
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "specialty",
            "crp_number",
            "bio",
            "phone",
            "avatar",
            "default_session_duration",
            "default_session_value",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login", "role"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "full_name",
            "specialty",
            "crp_number",
            "bio",
            "phone",
            "avatar",
            "default_session_duration",
            "default_session_value",
        ]


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
        return user


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh"])
        token_hash = refresh.get("hash_password")
        user_id = refresh.get("user_id")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidToken(_INVALID_TOKEN_MESSAGE)

        current_hash = get_md5_hash_password(user.password)
        if (
            not user.is_active
            or not token_hash
            or not secrets.compare_digest(str(token_hash), str(current_hash))
        ):
            raise InvalidToken(_INVALID_TOKEN_MESSAGE)

        data = {"access": str(refresh.access_token)}
        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            new_refresh = RefreshToken.for_user(user)
            data["access"] = str(new_refresh.access_token)
            data["refresh"] = str(new_refresh)

        return data


__all__ = [
    "ChangePasswordSerializer",
    "LoginSerializer",
    "PasswordResetConfirmSerializer",
    "PasswordResetRequestSerializer",
    "RegisterSerializer",
    "SafeTokenRefreshSerializer",
    "UserProfileSerializer",
    "UserProfileUpdateSerializer",
    "WorkingHoursSerializer",
]
