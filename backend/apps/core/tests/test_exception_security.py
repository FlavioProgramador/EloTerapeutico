"""Testes do tratamento seguro de exceções da API."""

import logging

import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory

from apps.core.exception_handler import custom_exception_handler
from apps.core.exceptions import (
    ApplicationOperationError,
    AuthorizationError,
    BusinessRuleViolation,
    DomainIntegrityError,
    ObjectNotFoundError,
)


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


@pytest.mark.parametrize(
    ("exc", "expected_status", "expected_code"),
    [
        (AuthorizationError("Acesso negado."), 403, "FORBIDDEN"),
        (ObjectNotFoundError("Paciente não encontrado."), 404, "NOT_FOUND"),
        (DomainIntegrityError("Estado incompatível."), 409, "DOMAIN_INTEGRITY_ERROR"),
        (BusinessRuleViolation("Regra não atendida."), 422, "BUSINESS_RULE_VIOLATION"),
    ],
)
def test_application_error_uses_semantic_status_and_code(exc, expected_status, expected_code):
    response = custom_exception_handler(exc, {})

    assert response.status_code == expected_status
    assert response.data["error"] == {
        "code": expected_code,
        "message": exc.detail,
        "details": None,
    }
    assert response["Cache-Control"] == "private, no-store, max-age=0"


def test_application_error_supports_custom_code_and_field_details():
    response = custom_exception_handler(
        BusinessRuleViolation(
            "Horário indisponível.",
            code="appointment_conflict",
            field="start_time",
        ),
        {},
    )

    assert response.status_code == 422
    assert response.data["error"] == {
        "code": "APPOINTMENT_CONFLICT",
        "message": "Horário indisponível.",
        "details": {"start_time": ["Horário indisponível."]},
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


def test_controlled_internal_error_does_not_log_sensitive_detail(caplog):
    sensitive_value = "cpf=52998224725 token=private-token"

    with caplog.at_level(logging.ERROR, logger="apps.core.exception_handler"):
        response = custom_exception_handler(
            ApplicationOperationError(sensitive_value, code="document_generation_failed"),
            {},
        )

    assert response.status_code == 500
    assert response.data["error"]["message"] == "Não foi possível concluir a operação."
    assert sensitive_value not in str(response.data)
    assert sensitive_value not in caplog.text
    assert "api_application_error" in caplog.text


def test_unhandled_exception_does_not_log_or_return_sensitive_message(caplog):
    sensitive_value = "cpf=52998224725 token=private-token"
    request = APIRequestFactory().get("/api/v1/test/")

    with caplog.at_level(logging.ERROR, logger="apps.core.exception_handler"):
        response = custom_exception_handler(
            RuntimeError(sensitive_value),
            {"request": request},
        )

    assert response.status_code == 500
    assert response.data["error"]["message"] == "Ocorreu um erro interno. Por favor, tente novamente."
    assert sensitive_value not in str(response.data)
    assert sensitive_value not in caplog.text
    assert "api_unhandled_exception" in caplog.text
