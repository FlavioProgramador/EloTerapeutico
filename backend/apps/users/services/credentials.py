"""Caso de uso de solicitação de redefinição de senha."""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.integrations.notifications import send_password_reset_email

from ..models import User

logger = logging.getLogger(__name__)


def request_password_reset(*, email: str) -> None:
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/forgot-password/reset?token={token}&uid={uid}"
    try:
        send_password_reset_email(
            recipient=email,
            user_name=user.full_name,
            reset_url=reset_url,
        )
    except Exception:
        logger.exception("Erro ao enviar e-mail de redefinição")
