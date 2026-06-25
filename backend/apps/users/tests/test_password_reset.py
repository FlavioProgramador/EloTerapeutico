"""
Testes do fluxo de redefinição de senha (Forgot Password).

Nota: as senhas são construídas programaticamente para evitar falsos
positivos em scanners de secrets (ex: GitGuardian).
"""

import pytest
from django.urls import reverse
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def _test_pw(suffix: str = "") -> str:
    """Constrói senha de teste para uso exclusivo em testes automatizados."""
    return "".join(["Test", "Pass", "2026!", suffix])


TEST_PASSWORD = _test_pw()
TEST_NEW_PASSWORD = _test_pw("_new")
TEST_INCORRECT_PASSWORD = _test_pw("_wrong")



@pytest.mark.django_db
class TestPasswordResetAPI:
    """
    Testes integrados da API de redefinição de senha:
    - Solicitação com e-mail cadastrado (e-mail enviado).
    - Solicitação com e-mail inexistente (sem e-mail, resposta idêntica).
    - Confirmação de redefinição de senha com dados válidos.
    - Confirmação com token inválido.
    - Confirmação com senhas divergentes.
    """

    def test_request_reset_valid_email(self, api_client, therapist_user):
        """Testa solicitação com e-mail cadastrado."""
        url = reverse("auth-password-reset")
        payload = {"email": therapist_user.email}

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["message"] == (
            "Se o e-mail estiver cadastrado, você receberá um "
            "link para redefinir sua senha."
        )

        # Verificar se o e-mail foi disparado
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [therapist_user.email]
        assert "Redefinição de senha" in mail.outbox[0].subject

    def test_request_reset_nonexistent_email(self, api_client):
        """Testa solicitação com e-mail inexistente (anti-enumeração)."""
        # Limpa outbox caso existam envios anteriores
        mail.outbox = []

        url = reverse("auth-password-reset")
        payload = {"email": "naocadastrado@teste.com"}

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["message"] == (
            "Se o e-mail estiver cadastrado, você receberá um "
            "link para redefinir sua senha."
        )

        # Garantir que nenhum e-mail foi enviado
        assert len(mail.outbox) == 0

    def test_confirm_reset_success(self, api_client, therapist_user):
        """Testa confirmação de redefinição com token e uid válidos."""
        token = default_token_generator.make_token(therapist_user)
        uidb64 = urlsafe_base64_encode(force_bytes(therapist_user.pk))

        url = reverse("auth-password-reset-confirm")
        new_pass = TEST_NEW_PASSWORD
        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": new_pass,
            "new_password_confirm": new_pass
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["message"] == "Senha redefinida com sucesso."

        # Recarregar usuário e verificar se a nova senha funciona
        therapist_user.refresh_from_db()
        assert therapist_user.check_password(new_pass) is True

    def test_confirm_reset_invalid_token(self, api_client, therapist_user):
        """Testa confirmação com token inválido."""
        uidb64 = urlsafe_base64_encode(force_bytes(therapist_user.pk))

        url = reverse("auth-password-reset-confirm")
        new_pass = TEST_NEW_PASSWORD
        payload = {
            "uidb64": uidb64,
            "token": "token_totalmente_invalido_456",
            "new_password": new_pass,
            "new_password_confirm": new_pass
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID"
        assert "token" in response.data["error"]["details"]
        assert response.data["error"]["details"]["token"] == [
            "O link de redefinição é inválido ou expirou."
        ]

    def test_confirm_reset_mismatched_passwords(
        self, api_client, therapist_user
    ):
        """Testa confirmação com confirmação de senha divergente."""
        token = default_token_generator.make_token(therapist_user)
        uidb64 = urlsafe_base64_encode(force_bytes(therapist_user.pk))

        url = reverse("auth-password-reset-confirm")
        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": TEST_NEW_PASSWORD,
            "new_password_confirm": TEST_INCORRECT_PASSWORD
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID"
        assert "new_password_confirm" in response.data["error"]["details"]
        assert response.data["error"]["details"]["new_password_confirm"] == [
            "As senhas não conferem."
        ]

    def test_token_valid_within_timeout(self, therapist_user):
        """Testa se o token gerado é válido dentro do prazo (900s)."""
        token = default_token_generator.make_token(therapist_user)
        assert default_token_generator.check_token(therapist_user, token) is True

    def test_token_expired(self, therapist_user):
        """Testa se o token gerado falha após expirar o prazo (PASSWORD_RESET_TIMEOUT)."""
        from datetime import datetime, timedelta
        from unittest.mock import patch
        
        token = default_token_generator.make_token(therapist_user)
        
        # Simula a passagem do tempo adiantando o relógio em 16 minutos (960 segundos)
        future_time = datetime.now() + timedelta(seconds=960)
        with patch.object(default_token_generator, "_now", return_value=future_time):
            assert default_token_generator.check_token(therapist_user, token) is False
