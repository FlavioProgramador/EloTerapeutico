"""Caso de uso de solicitação de redefinição de senha."""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.communications.infrastructure.messaging.email import send_password_reset_email

from ..models import User

logger = logging.getLogger(__name__)


def request_password_reset(*, email: str) -> None:
    """Solicita redefinição de senha sem permitir enumeração de contas.

    Quando existe um usuário ativo com o e-mail informado, o serviço gera o
    token nativo do Django, monta a URL do frontend e delega o envio ao adapter
    de e-mail. Contas inexistentes ou inativas encerram o fluxo silenciosamente
    para que a resposta pública seja indistinguível.

    Args:
        email: Endereço informado pelo solicitante.

    Returns:
        ``None``. O resultado não indica se a conta existe.

    Side Effects:
        Pode enviar um e-mail de redefinição de senha para uma conta ativa.
        Falhas do provider são registradas apenas com o tipo da exceção.
    """
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
    except Exception as exc:
        logger.error(
            "password_reset_email_failed",
            extra={"exception_type": exc.__class__.__name__},
        )
