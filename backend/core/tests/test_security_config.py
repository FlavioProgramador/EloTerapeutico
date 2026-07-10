import pytest
from django.core.exceptions import ImproperlyConfigured

from core.security_config import require_distinct_secrets, require_strong_secret


def test_rejeita_placeholder_de_arquivo_exemplo():
    with pytest.raises(ImproperlyConfigured, match="não pode usar valor padrão"):
        require_strong_secret("SECRET_KEY", "changeme")


def test_rejeita_segredo_curto():
    with pytest.raises(ImproperlyConfigured, match="pelo menos 32 caracteres"):
        require_strong_secret("JWT_SECRET", "curto")


def test_aceita_segredo_longo_e_nao_padrao():
    value = "segredo-unico-de-producao-com-mais-de-32-caracteres"

    assert require_strong_secret("SECRET_KEY", value) == value


def test_rejeita_reutilizacao_de_segredos():
    same_secret = "segredo-repetido-com-mais-de-32-caracteres"

    with pytest.raises(ImproperlyConfigured, match="devem usar segredos distintos"):
        require_distinct_secrets(
            {
                "SECRET_KEY": same_secret,
                "JWT_SECRET": same_secret,
            }
        )


def test_aceita_segredos_distintos():
    require_distinct_secrets(
        {
            "SECRET_KEY": "segredo-django-distinto-com-mais-de-32-caracteres",
            "JWT_SECRET": "segredo-jwt-distinto-com-mais-de-32-caracteres",
        }
    )
