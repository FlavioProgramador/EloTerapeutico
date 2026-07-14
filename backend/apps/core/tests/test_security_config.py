import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.core.security_config import require_distinct_secrets, require_strong_secret


def _fake_secret(label: str) -> str:
    """Gera valor fictício longo sem manter um token estático no repositório."""

    return "-".join([label, "teste", "seguro", "x" * 32])


def test_rejeita_placeholder_de_arquivo_exemplo():
    with pytest.raises(ImproperlyConfigured, match="não pode usar valor padrão"):
        require_strong_secret("SECRET_KEY", "changeme")


def test_rejeita_segredo_curto():
    with pytest.raises(ImproperlyConfigured, match="pelo menos 32 caracteres"):
        require_strong_secret("JWT_SECRET", "curto")


def test_aceita_segredo_longo_e_nao_padrao():
    value = _fake_secret("producao")

    assert require_strong_secret("SECRET_KEY", value) == value


def test_rejeita_reutilizacao_de_segredos():
    same_secret = _fake_secret("repetido")

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
            "SECRET_KEY": _fake_secret("django"),
            "JWT_SECRET": _fake_secret("jwt"),
        }
    )
