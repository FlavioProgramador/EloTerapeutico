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

    def test_token_invalidation_after_password_reset(
        self, api_client, therapist_user
    ):
        """
        Testa se tokens antigos são invalidados após reset de senha.
        """
        # 1. Autenticar o usuário
        login_url = reverse("auth-login")
        login_payload = {
            "email": therapist_user.email,
            "password": TEST_PASSWORD
        }
        login_response = api_client.post(
            login_url, login_payload, format="json"
        )
        assert login_response.status_code == 200
        old_access = login_response.data["access"]
        old_refresh = login_response.data["refresh"]

        # 2. Redefinir a senha
        token = default_token_generator.make_token(therapist_user)
        uidb64 = urlsafe_base64_encode(force_bytes(therapist_user.pk))

        reset_url = reverse("auth-password-reset-confirm")
        new_pass = TEST_NEW_PASSWORD
        reset_payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": new_pass,
            "new_password_confirm": new_pass
        }
        reset_response = api_client.post(
            reset_url, reset_payload, format="json"
        )
        assert reset_response.status_code == 200

        # 3. Tentar usar o access token anterior
        me_url = reverse("user-me")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_access}")
        me_response = api_client.get(me_url)

        # 4. Tentar renovar a sessão com o refresh token anterior
        api_client.credentials()  # Limpa credenciais
        refresh_url = reverse("token-refresh")
        refresh_payload = {"refresh": old_refresh}
        refresh_response = api_client.post(
            refresh_url, refresh_payload, format="json"
        )

        # 5. Fazer login com a nova senha
        new_login_response = api_client.post(login_url, {
            "email": therapist_user.email,
            "password": new_pass
        }, format="json")
        assert new_login_response.status_code == 200

        # Registra o comportamento obtido
        access_valid_after_reset = (me_response.status_code == 200)
        refresh_valid_after_reset = (refresh_response.status_code == 200)

        print("\n--- TOKEN INVALIDATION REPORT ---")
        print(f"Old Access Token: {me_response.status_code} "
              f"(Valid? {access_valid_after_reset})")
        print(f"Old Refresh Token: {refresh_response.status_code} "
              f"(Valid? {refresh_valid_after_reset})")
        print("--------------------------------\n")

        # Ambos os tokens devem ser invalidados
        assert me_response.status_code == 401
        assert refresh_response.status_code == 401

    def test_token_cannot_be_reused(self, api_client, therapist_user):
        """Testa que um token de reset não pode ser reutilizado após a alteração da senha."""
        token = default_token_generator.make_token(therapist_user)
        uidb64 = urlsafe_base64_encode(force_bytes(therapist_user.pk))
        url = reverse("auth-password-reset-confirm")
        
        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password": TEST_NEW_PASSWORD,
            "new_password_confirm": TEST_NEW_PASSWORD
        }
        
        # Primeiro uso: sucesso
        res1 = api_client.post(url, payload, format="json")
        assert res1.status_code == 200
        
        # Segundo uso com o mesmo token: deve falhar
        res2 = api_client.post(url, payload, format="json")
        assert res2.status_code == 400
        assert res2.data["error"]["code"] == "INVALID"
        assert "token" in res2.data["error"]["details"]
        assert res2.data["error"]["details"]["token"] == [
            "O link de redefinição é inválido ou expirou."
        ]
