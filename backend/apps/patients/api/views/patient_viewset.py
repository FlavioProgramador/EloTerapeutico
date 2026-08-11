"""ViewSet canônico de pacientes com isolamento obrigatório por organização."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.billing.services.features import enforce_patient_limit
from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability
from apps.organizations.services.tenant_context import ensure_request_organization
from apps.patients.api.serializers.legacy_serializers import (
    PatientCreateUpdateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
)
from apps.patients.exceptions import InvalidPatientState
from apps.patients.models import Patient
from apps.patients.selectors.patients import patients_accessible_to
from apps.patients.services.access_control import can_access_patient, can_manage_patient
from apps.patients.services.lifecycle import deactivate as deactivate_patient
from apps.patients.services.lifecycle import restore as restore_patient

from .legacy_views import PatientViewSet as LegacyPatientViewSet


class AdministrativePatientSerializer(serializers.ModelSerializer):
    """Dados mínimos para recepção, financeiro e perfis somente leitura."""

    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "whatsapp",
            "status",
            "therapist_name",
            "is_active",
        ]
        read_only_fields = fields


class TenantPatientCreateUpdateSerializer(PatientCreateUpdateSerializer):
    """Valida unicidade e vínculos profissionais dentro do tenant ativo."""

    def validate_cpf(self, value):
        if not value:
            return value
        from apps.core.validators import validate_cpf

        validate_cpf(value)
        clean_cpf = re.sub(r"\D", "", value)
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if organization is None:
            raise serializers.ValidationError(
                "Selecione uma organização antes de cadastrar o paciente."
            )
        queryset = Patient.all_objects.filter(
            organization=organization,
            cpf=clean_cpf,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "Um paciente com este CPF já está cadastrado nesta organização."
            )
        return clean_cpf

    def validate_therapist(self, therapist):
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if organization is None:
            raise serializers.ValidationError("Organização ativa não encontrada.")
        is_professional = OrganizationMembership.objects.filter(
            organization=organization,
            user=therapist,
            status=OrganizationMembership.Status.ACTIVE,
            role__in=[
                OrganizationMembership.Role.OWNER,
                OrganizationMembership.Role.ADMIN,
                OrganizationMembership.Role.THERAPIST,
            ],
        ).exists()
        if not is_professional:
            raise serializers.ValidationError(
                "O terapeuta selecionado não pertence à organização."
            )
        return therapist

    def validate(self, attrs):
        request = self.context.get("request")
        membership = getattr(request, "organization_membership", None)
        if (
            membership is not None
            and membership.role == OrganizationMembership.Role.THERAPIST
            and "therapist" not in attrs
            and self.instance is None
        ):
            attrs["therapist"] = request.user
        return super().validate(attrs)


class OrganizationPatientPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        _, membership = ensure_request_organization(
            request=request,
            required=True,
        )
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return has_capability(membership, "patients.view")
        if getattr(view, "action", "") in {"deactivate", "restore"}:
            return has_capability(membership, "patients.update")
        if request.method == "POST":
            return has_capability(membership, "patients.create")
        if request.method in {"PUT", "PATCH"}:
            return has_capability(membership, "patients.update")
        if request.method == "DELETE":
            # Permite chegar ao queryset tenant-aware. Registros fora do escopo
            # retornam 404; a capability de arquivamento é verificada no objeto.
            return has_capability(membership, "patients.view")
        return False

    def has_object_permission(self, request, view, obj):
        _, membership = ensure_request_organization(
            request=request,
            required=True,
        )
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return can_access_patient(
                request.user,
                obj,
                membership=membership,
                allow_secretary=True,
            )
        if request.method == "DELETE":
            return can_access_patient(
                request.user,
                obj,
                membership=membership,
                allow_secretary=True,
            ) and has_capability(membership, "patients.archive")
        return can_manage_patient(
            request.user,
            obj,
            membership=membership,
        )


class PatientViewSet(LegacyPatientViewSet):
    permission_classes = [OrganizationPatientPermission]

    def get_queryset(self):
        include_deleted = self.action == "restore"
        return patients_accessible_to(
            self.request.user,
            organization=getattr(self.request, "organization", None),
            membership=getattr(self.request, "organization_membership", None),
            include_deleted=include_deleted,
        ).order_by("full_name")

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return TenantPatientCreateUpdateSerializer
        membership = getattr(self.request, "organization_membership", None)
        if membership and membership.role in {
            OrganizationMembership.Role.RECEPTIONIST,
            OrganizationMembership.Role.FINANCE,
            OrganizationMembership.Role.VIEWER,
        }:
            return AdministrativePatientSerializer
        if self.action == "list":
            return PatientListSerializer
        return PatientDetailSerializer

    def perform_create(self, serializer):
        organization = getattr(self.request, "organization", None)
        membership = getattr(self.request, "organization_membership", None)
        if organization is None or membership is None:
            raise DRFValidationError(
                {"detail": "Selecione uma organização antes de cadastrar o paciente."}
            )

        therapist = serializer.validated_data.get("therapist")
        if membership.role == OrganizationMembership.Role.THERAPIST:
            therapist = self.request.user
        if therapist is None:
            raise DRFValidationError(
                {"therapist": "Selecione um terapeuta da organização."}
            )

        subscription_owner = organization.created_by or self.request.user
        try:
            enforce_patient_limit(subscription_owner)
        except DjangoValidationError as exc:
            raise DRFValidationError({"detail": exc.messages[0]}) from exc

        serializer.save(organization=organization, therapist=therapist)
        self._record_instance(
            AuditLog.Action.CREATE,
            serializer.instance,
            on_commit=True,
        )

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        try:
            deactivate_patient(self.get_object())
        except InvalidPatientState as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Paciente desativado com sucesso."})

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        try:
            restore_patient(self.get_object())
        except InvalidPatientState as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Paciente restaurado com sucesso."})
