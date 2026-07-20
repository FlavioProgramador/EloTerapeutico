from django.core.exceptions import ValidationError

from apps.core.api.exceptions import custom_exception_handler


def test_django_validation_error_preserves_safe_field_details():
    response = custom_exception_handler(
        ValidationError({"patient": "Paciente fora do escopo."}),
        {},
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"
    assert response.data["error"]["details"] == {
        "patient": ["Paciente fora do escopo."]
    }
