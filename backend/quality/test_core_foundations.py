from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed

from apps.core.exceptions import custom_exception_handler
from apps.core.pagination import StandardResultsPagination


def test_exception_handler_wraps_method_not_allowed():
    response = custom_exception_handler(MethodNotAllowed("TRACE"), {})

    assert response.status_code == 405
    assert response.data["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert response.data["error"]["details"]["detail"]


def test_exception_handler_handles_django_validation_error():
    response = custom_exception_handler(ValidationError("Campo inválido."), {})

    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"
    assert "Campo inválido" in response.data["error"]["message"]


def test_exception_handler_handles_permission_and_not_found():
    denied = custom_exception_handler(PermissionDenied(), {})
    missing = custom_exception_handler(Http404(), {})

    assert denied.status_code == 403
    assert denied.data["error"]["code"] == "PERMISSION_DENIED"
    assert missing.status_code == 404
    assert missing.data["error"]["code"] == "NOT_FOUND"


def test_pagination_schema_exposes_metadata_contract():
    schema = StandardResultsPagination().get_paginated_response_schema(
        {"type": "array", "items": {"type": "object"}}
    )

    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"pagination", "results"}
    assert set(schema["properties"]["pagination"]["properties"]) == {
        "count",
        "total_pages",
        "current_page",
        "next",
        "previous",
    }
