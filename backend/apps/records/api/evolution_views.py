"""Endpoints canônicos do fluxo de evoluções clínicas."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services.access_logging import AuditLog, log_access
from apps.records.api.views.clinical_views import ClinicalPatientMixin, RecordPagination

from ..selectors.evolutions import (
    available_appointments_for_evolution,
    evolutions_for_patient,
)
from ..services.evolutions import archive_evolution
from .evolution_serializers import (
    EvolutionAppointmentOptionSerializer,
    EvolutionFlowSerializer,
)


class PatientEvolutionFlowView(ClinicalPatientMixin, APIView):
    pagination_class = RecordPagination

    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = evolutions_for_patient(
            patient=patient,
            user=request.user,
            status=request.query_params.get("status"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = EvolutionFlowSerializer(
            page,
            many=True,
            context={"request": request, "patient": patient},
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        if not (request.user.is_therapist or request.user.is_admin_role):
            self.permission_denied(
                request,
                message="Seu perfil não pode criar registros clínicos.",
            )
        serializer = EvolutionFlowSerializer(
            data=request.data,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.save()
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=evolution,
            obj_repr=(f"Evolução #{evolution.id} criada; confidencial={evolution.is_confidential}"),
        )
        return Response(
            EvolutionFlowSerializer(
                evolution,
                context={"request": request, "patient": patient},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EvolutionFlowDetailView(ClinicalPatientMixin, APIView):
    def get(self, request, pk):
        evolution = self.get_evolution(pk)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=evolution,
            obj_repr=f"Visualização da evolução #{evolution.id}",
        )
        return Response(
            EvolutionFlowSerializer(
                evolution,
                context={"request": request, "patient": evolution.patient},
            ).data
        )

    def patch(self, request, pk):
        evolution = self.get_evolution(pk)
        before = evolution.is_confidential
        serializer = EvolutionFlowSerializer(
            evolution,
            data=request.data,
            partial=True,
            context={"request": request, "patient": evolution.patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=evolution,
            obj_repr=(
                f"Evolução #{evolution.id} atualizada; "
                f"confidencialidade_alterada={before != evolution.is_confidential}; "
                f"confidencial={evolution.is_confidential}"
            ),
        )
        return Response(
            EvolutionFlowSerializer(
                evolution,
                context={"request": request, "patient": evolution.patient},
            ).data
        )

    def delete(self, request, pk):
        evolution = self.get_evolution(pk)
        archive_evolution(evolution=evolution, actor=request.user)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=evolution,
            obj_repr=f"Evolução #{evolution.id} arquivada logicamente",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PatientEvolutionAppointmentOptionsView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = available_appointments_for_evolution(
            patient=patient,
            include_cancelled=(request.query_params.get("include_cancelled") == "true"),
        )
        serializer = EvolutionAppointmentOptionSerializer(queryset, many=True)
        return Response(serializer.data)
