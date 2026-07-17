from pathlib import Path


BILLING_ROOT = Path(__file__).resolve().parents[1]


def test_billing_canonical_packages_exist():
    required_paths = [
        BILLING_ROOT / "api" / "authentication" / "__init__.py",
        BILLING_ROOT / "api" / "access" / "decorators.py",
        BILLING_ROOT / "api" / "public" / "urls.py",
        BILLING_ROOT / "api" / "public" / "views" / "registration.py",
        BILLING_ROOT / "api" / "public" / "views" / "webhooks.py",
        BILLING_ROOT / "api" / "v1" / "urls.py",
        BILLING_ROOT / "integrations" / "asaas" / "client.py",
        BILLING_ROOT / "integrations" / "asaas" / "exceptions.py",
        BILLING_ROOT / "integrations" / "asaas" / "security.py",
        BILLING_ROOT
        / "integrations"
        / "asaas"
        / "webhooks"
        / "processor.py",
        BILLING_ROOT
        / "integrations"
        / "asaas"
        / "webhooks"
        / "payments.py",
        BILLING_ROOT
        / "integrations"
        / "asaas"
        / "webhooks"
        / "subscriptions.py",
    ]

    missing = [
        str(path.relative_to(BILLING_ROOT))
        for path in required_paths
        if not path.exists()
    ]
    assert not missing, f"Caminhos canônicos ausentes: {missing}"


def test_asaas_package_root_has_no_eager_webhook_import():
    package_init = BILLING_ROOT / "integrations" / "asaas" / "__init__.py"
    source = package_init.read_text(encoding="utf-8")

    assert "from .webhooks import" not in source
    assert "import .webhooks" not in source


def test_legacy_billing_facades_remain_thin():
    facades_with_limits = {
        BILLING_ROOT
        / "infrastructure"
        / "payments"
        / "asaas"
        / "client.py": 20,
        BILLING_ROOT
        / "integrations"
        / "webhooks"
        / "asaas"
        / "__init__.py": 60,
        BILLING_ROOT
        / "integrations"
        / "webhooks"
        / "asaas"
        / "payments.py": 20,
        BILLING_ROOT / "api" / "public" / "registration.py": 20,
        BILLING_ROOT / "api" / "public" / "webhooks.py": 20,
        BILLING_ROOT / "authentication" / "__init__.py": 20,
        BILLING_ROOT / "security" / "__init__.py": 20,
        BILLING_ROOT / "webhooks" / "asaas.py": 35,
    }

    for path, maximum_lines in facades_with_limits.items():
        assert path.exists(), f"Fachada de compatibilidade ausente: {path}"
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        assert line_count <= maximum_lines, (
            f"Fachada contém implementação excessiva: {path} "
            f"({line_count} > {maximum_lines})"
        )


def test_public_billing_urls_are_flattened_into_v1_contract():
    urls_path = BILLING_ROOT / "api" / "v1" / "urls.py"
    source = urls_path.read_text(encoding="utf-8")

    assert "public_urlpatterns" in source
    assert "*public_urlpatterns" in source
    assert 'include("apps.billing.api.public.urls")' not in source


def test_canonical_client_is_the_only_full_asaas_client():
    canonical = BILLING_ROOT / "integrations" / "asaas" / "client.py"
    compatibility = (
        BILLING_ROOT / "infrastructure" / "payments" / "asaas" / "client.py"
    )

    assert len(canonical.read_text(encoding="utf-8").splitlines()) > 100
    compatibility_source = compatibility.read_text(encoding="utf-8")
    assert "class AsaasGateway" not in compatibility_source
    assert (
        "from apps.billing.integrations.asaas.client import"
        in compatibility_source
    )
