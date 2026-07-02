"""
apps/records/views.py
Views e ViewSets para o app de Prontuários Eletrônicos (Records).
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.audit import AuditLogMixin, AuditLog, log_access
from .models import Anamnesis, Evolution
from .serializers import (
    AnamnesisSerializer,
    EvolutionListSerializer,
    EvolutionDetailSerializer,
    EvolutionCreateSerializer,
    EvolutionUpdateSerializer,
    EvolutionAddendumSerializer,
)


class AnamnesisView(generics.GenericAPIView):
    """
    View para recuperar, criar ou atualizar a anamnese de um paciente.
    Acessível via /api/v1/patients/{patient_id}/anamnesis/
    """

    serializer_class = AnamnesisSerializer
    permission_classes = [IsAuthenticated]

    def _get_patient(self, patient_id):
        from apps.patients.models import Patient

        # Obter o paciente ou retornar 404
        patient = get_object_or_404(Patient, id=patient_id)

        # Validar permissão: apenas o terapeuta responsável ou admin
        user = self.request.user
        if not user.is_admin_role and patient.therapist != user:
            self.permission_denied(
                self.request,
                message="Você não tem permissão para acessar o prontuário deste paciente.",
            )
        return patient

    def get(self, request, patient_id, *args, **kwargs):
        patient = self._get_patient(patient_id)
        try:
            anamnesis = Anamnesis.objects.get(patient=patient)
        except Anamnesis.DoesNotExist:
            return Response(
                {"detail": "Anamnese não encontrada para este paciente."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Auditoria: registrando leitura de anamnese
        log_access(request, AuditLog.Action.VIEW, obj=anamnesis)

        serializer = self.get_serializer(anamnesis)
        return Response(serializer.data)

    def post(self, request, patient_id, *args, **kwargs):
        patient = self._get_patient(patient_id)
        if Anamnesis.objects.filter(patient=patient).exists():
            return Response(
                {
                    "detail": "Anamnese já existe para este paciente. Use PUT ou PATCH para atualizar."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data["patient_id"] = patient.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        anamnesis = serializer.save(created_by=request.user, patient=patient)

        # Auditoria: registrando criação
        log_access(request, AuditLog.Action.CREATE, obj=anamnesis)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, patient_id, *args, **kwargs):
        patient = self._get_patient(patient_id)
        anamnesis = get_object_or_404(Anamnesis, patient=patient)

        serializer = self.get_serializer(anamnesis, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Auditoria: modificação
        log_access(request, AuditLog.Action.UPDATE, obj=anamnesis)

        return Response(serializer.data)

    def patch(self, request, patient_id, *args, **kwargs):
        patient = self._get_patient(patient_id)
        anamnesis = get_object_or_404(Anamnesis, patient=patient)

        serializer = self.get_serializer(anamnesis, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Auditoria: modificação parcial
        log_access(request, AuditLog.Action.UPDATE, obj=anamnesis)

        return Response(serializer.data)


class EvolutionViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """
    ViewSet para as evoluções clínicas das sessões.
    Auditoria automática via AuditLogMixin.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Evolution.objects.none()

        patient_id = self.request.query_params.get("patient")
        if not patient_id:
            # Caso não informe o paciente, admin vê tudo; terapeuta só vê as criadas por ele
            if user.is_admin_role:
                return Evolution.objects.all()
            return Evolution.objects.filter(created_by=user)

        from apps.patients.models import Patient

        patient = get_object_or_404(Patient, id=patient_id)

        # Apenas o terapeuta dono ou admin pode ver evoluções do paciente
        if not user.is_admin_role and patient.therapist != user:
            self.permission_denied(
                self.request,
                message="Você não tem permissão para acessar o prontuário deste paciente.",
            )

        return Evolution.objects.filter(patient=patient)

    def get_serializer_class(self):
        if self.action == "list":
            return EvolutionListSerializer
        if self.action == "create":
            return EvolutionCreateSerializer
        if self.action in ["update", "partial_update"]:
            return EvolutionUpdateSerializer
        return EvolutionDetailSerializer

    def perform_create(self, serializer):
        # Vincula a evolução ao usuário logado
        instance = serializer.save(created_by=self.request.user)
        # AuditLogMixin realiza auditoria automaticamente, mas chamamos explicitamente
        # para garantir consistência no log de auditoria
        log_access(self.request, AuditLog.Action.CREATE, obj=instance)

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        # Apenas o terapeuta que criou ou admin pode atualizar a evolução
        if not user.is_admin_role and instance.created_by != user:
            self.permission_denied(
                self.request,
                message="Somente o terapeuta que criou esta evolução pode editá-la.",
            )

        if not instance.can_be_edited():
            return Response(
                {
                    "detail": "Esta evolução está bloqueada para edição (limite de 48h atingido ou bloqueada manualmente)."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_instance = serializer.save()
        log_access(self.request, AuditLog.Action.UPDATE, obj=updated_instance)

    def perform_destroy(self, instance):
        # Regulamentação CFP/LGPD: evoluções de prontuário não devem ser deletadas do DB
        self.permission_denied(
            self.request,
            message="Registros de prontuário clínico (evoluções) não podem ser excluídos do sistema.",
        )

    @action(detail=True, methods=["post"], url_path="addendum")
    def add_addendum(self, request, pk=None):
        """
        Adiciona um aditivo a uma evolução bloqueada.
        POST /api/v1/records/evolutions/{id}/addendum/
        """
        evolution = self.get_object()

        # Bloqueia a evolução no momento se já expirou o limite de 48 horas
        if not evolution.is_locked and not evolution.can_be_edited():
            evolution.lock()

        # Aditivos só podem ser inseridos se a evolução estiver travada
        if not evolution.is_locked:
            return Response(
                {
                    "detail": "A evolução ainda não está bloqueada. Edite o conteúdo principal diretamente."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EvolutionAddendumSerializer(
            data=request.data, context={"request": request, "evolution": evolution}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(evolution=evolution, created_by=request.user)

        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=evolution,
            obj_repr=f"Aditivo criado por {request.user.full_name} para {evolution}",
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="export_pdf")
    def export_pdf(self, request, pk=None):
        """
        Exporta os registros clínicos da evolução e seus aditivos como PDF.
        GET /api/v1/records/evolutions/{id}/export_pdf/
        """
        # TODO: Integrar com ReportLab/Weasyprint para geração do PDF criptografado
        return Response(
            {
                "detail": "Exportação em PDF do Prontuário Clínico em desenvolvimento (501 Not Implemented)."
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
