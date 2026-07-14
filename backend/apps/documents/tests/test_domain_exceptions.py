from types import SimpleNamespace

import pytest

from apps.core.exceptions import AuthorizationError, BusinessRuleViolation, DomainIntegrityError
from apps.documents.models import DocumentTemplate
from apps.documents.services.core_services import ensure_patient_access, ensure_template_access


def test_patient_access_uses_authorization_error():
    actor = SimpleNamespace(id=10, is_secretary=False)
    patient = SimpleNamespace(therapist_id=99)

    with pytest.raises(AuthorizationError) as error:
        ensure_patient_access(actor=actor, patient=patient)

    assert error.value.status_code == 403
    assert error.value.code == "document_patient_access_denied"


def test_inactive_template_uses_domain_integrity_error():
    actor = SimpleNamespace(id=10)
    template = SimpleNamespace(
        status=DocumentTemplate.Status.INACTIVE,
        is_library_template=False,
        owner_id=10,
    )

    with pytest.raises(DomainIntegrityError) as error:
        ensure_template_access(actor=actor, template=template)

    assert error.value.status_code == 409
    assert error.value.code == "document_template_inactive"


def test_library_template_requires_import_as_business_rule():
    actor = SimpleNamespace(id=10)
    template = SimpleNamespace(
        status=DocumentTemplate.Status.ACTIVE,
        is_library_template=True,
        owner_id=None,
    )

    with pytest.raises(BusinessRuleViolation) as error:
        ensure_template_access(actor=actor, template=template)

    assert error.value.status_code == 422
    assert error.value.code == "document_template_import_required"
