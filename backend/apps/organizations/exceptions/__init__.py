"""Erros semânticos do domínio de organizações."""

from rest_framework.exceptions import APIException


class OrganizationContextRequiredError(APIException):
    status_code = 400
    default_detail = "Selecione uma organização para continuar."
    default_code = "organization_context_required"


class OrganizationAccessDeniedError(APIException):
    status_code = 404
    default_detail = "Organização não encontrada."
    default_code = "organization_not_found"


class OrganizationSuspendedError(APIException):
    status_code = 403
    default_detail = "Esta organização está suspensa."
    default_code = "organization_suspended"


class MembershipNotActiveError(APIException):
    status_code = 403
    default_detail = "Seu acesso a esta organização não está ativo."
    default_code = "membership_not_active"


class LastOwnerRemovalError(APIException):
    status_code = 409
    default_detail = "Não é possível remover o último proprietário ativo."
    default_code = "last_owner_removal"


class InvitationExpiredError(APIException):
    status_code = 410
    default_detail = "Este convite expirou."
    default_code = "invitation_expired"


class InvitationAlreadyUsedError(APIException):
    status_code = 409
    default_detail = "Este convite já foi utilizado."
    default_code = "invitation_already_used"


class InvitationInvalidError(APIException):
    status_code = 404
    default_detail = "Convite inválido."
    default_code = "invitation_invalid"


class OnboardingIncompleteError(APIException):
    status_code = 422
    default_detail = "Preencha os campos obrigatórios antes de concluir o onboarding."
    default_code = "onboarding_incomplete"


class CrossTenantRelationshipError(APIException):
    status_code = 409
    default_detail = "Os recursos informados pertencem a organizações diferentes."
    default_code = "cross_tenant_relationship"


__all__ = [
    "CrossTenantRelationshipError",
    "InvitationAlreadyUsedError",
    "InvitationExpiredError",
    "InvitationInvalidError",
    "LastOwnerRemovalError",
    "MembershipNotActiveError",
    "OnboardingIncompleteError",
    "OrganizationAccessDeniedError",
    "OrganizationContextRequiredError",
    "OrganizationSuspendedError",
]
