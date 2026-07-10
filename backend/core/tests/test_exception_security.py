"""Testes do tratamento seguro de exceções da API."""

import logging

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory

from core.exceptions import custom_exception_handler


def test_validation_error_has_request_id_and_no_store_headers():
    request = APIRequestFactory().get(
        "/api/v1/test/",
        HTTP_X_REQUEST_ID="request-test-123",
    )

    response = custom_exception_handler(
        DRFValidationError({"field": ["Valor inválido."]}),
        {"request": request},
    )

    assert response.status_code == 400
    assert response["X-Request-ID"] == "request-test-123"
    assert response["Cache-Control"] == "private, no-store, max-age=0"
    assert response["Pragma"] == "no-cache"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response.data == {
        "error": {
            "code": "INVALID",
            "message": "field: Valor inválido.",
            "details": {"field": ["Valor inválido."]},
        }
    }


def test_invalid_request_id_is_not_reflected():
    malicious_request_id = "invalid\r\nInjected-Header: true"
    request = APIRequestFactory().get(
        "/api/v1/test/",
        HTTP_X_REQUEST_ID=malicious_request_id,
    )

    response = custom_exception_handler(
        DRFValidationError({"field": ["Inválido."]}),
        {"request": request},
    )

    generated_request_id = response["X-Request-ID"]
    assert generated_request_id != malicious_request_id
    assert len(generated_request_id) == 32
    assert generated_request_id.isalnum()


def test_unhandled_exception_does_not_log_or_return_sensitive_message(caplog):
    sensitive_value = "cpf=52998224725 token=private-token"
    request = APIRequestFactory().get("/api/v1/test/")

    with caplog.at_level(logging.ERROR, logger="core.exceptions"):
        response = custom_exception_handler(
            RuntimeError(sensitive_value),
            {"request": request},
        )

    assert response.status_code == 500
    assert response.data["error"]["message"] == "Ocorreu um erro interno. Por favor, tente novamente."
    assert sensitive_value not in str(response.data)
    assert sensitive_value not in caplog.text
    assert "api_unhandled_exception" in caplog.text
