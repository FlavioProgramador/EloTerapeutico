"""Integração isolada de envio de e-mails transacionais."""

from django.conf import settings
from django.core.mail import send_mail


def send_password_reset_email(*, recipient: str, user_name: str, reset_url: str) -> None:
    subject = "Redefinição de senha — Elo Terapêutico"
    message = (
        f"Olá, {user_name}.\n\n"
        "Você solicitou a redefinição de senha para sua conta no Elo Terapêutico.\n"
        "Para prosseguir, acesse o link abaixo:\n"
        f"{reset_url}\n\n"
        "Este link é válido por tempo limitado.\n"
        "Caso não tenha solicitado, desconsidere este e-mail.\n"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )
