#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$(dirname 'backend/apps/financeiro/api/filters.py')"
cat > 'backend/apps/financeiro/api/filters.py' <<'__ELO_0000__'
"""Filtros de consulta do módulo financeiro."""

from django.db.models import Q
from django_filters import rest_framework as filters

from .models import FinancialTransaction


class FinancialTransactionFilter(filters.FilterSet):
    created_at_gte = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")
    due_date_gte = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_date_lte = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    start_date = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")
    recurring = filters.BooleanFilter(field_name="is_recurring")

    class Meta:
        model = FinancialTransaction
        fields = [
            "transaction_type",
            "payment_status",
            "payment_method",
            "category",
            "category_ref",
            "patient",
            "therapist",
            "source",
            "beneficiary",
            "recurring",
            "created_at_gte",
            "created_at_lte",
            "due_date_gte",
            "due_date_lte",
            "start_date",
            "end_date",
        ]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(description__icontains=value)
            | Q(beneficiary__icontains=value)
            | Q(patient__full_name__icontains=value)
        )
__ELO_0000__

mkdir -p "$(dirname 'backend/apps/financeiro/api/financial_viewsets.py')"
cat > 'backend/apps/financeiro/api/financial_viewsets.py' <<'__ELO_0001__'
"""ViewSets dos recursos financeiros além do livro de transações."""

from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from ..models import Charge, FinancialCategory, MonthlySubscription
from ..services.charges import (
    build_whatsapp_url,
    create_charge,
    eligible_sessions,
    generate_monthly_charges,
    mark_whatsapp_opened,
)
from ..services.subscriptions import (
    change_subscription_status,
    create_subscription,
    process_due_subscription,
)
from .serializers import (
    ChargeCreateSerializer,
    ChargeDetailSerializer,
    ChargeListSerializer,
    EligibleAppointmentSerializer,
    FinancialCategorySerializer,
    GenerateMonthlyChargesSerializer,
    MonthlySubscriptionSerializer,
)
from .views import FinancialPermission


def _service_call(callable_, **kwargs):
    try:
        return callable_(**kwargs)
    except DjangoValidationError as exc:
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        raise ValidationError(detail) from exc


class FinancialCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialCategorySerializer
    permission_classes = [FinancialPermission]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = FinancialCategory.objects.all()
        if user.is_admin_role or user.is_secretary:
            therapist_id = self.request.query_params.get("therapist")
            return queryset.filter(therapist_id=therapist_id) if therapist_id else queryset
        return queryset.filter(therapist=user)


class ChargeViewSet(viewsets.ModelViewSet):
    permission_classes = [FinancialPermission]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Charge.objects.select_related(
            "patient", "professional", "transaction", "therapist"
        ).prefetch_related("items__appointment")
        if user.is_admin_role or user.is_secretary:
            professional_id = self.request.query_params.get("professional")
            return queryset.filter(professional_id=professional_id) if professional_id else queryset
        return queryset.filter(therapist=user)

    def get_serializer_class(self):
        if self.action == "create":
            return ChargeCreateSerializer
        if self.action == "retrieve":
            return ChargeDetailSerializer
        return ChargeListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        professional = data["professional"]
        charge = _service_call(
            create_charge,
            therapist=professional,
            actor=request.user,
            patient_id=data["patient"].pk,
            appointment_ids=data["appointment_ids"],
            due_date=data["due_date"],
            payment_link=data.get("payment_link", ""),
            notes=data.get("notes", ""),
            description=data.get("description", ""),
        )
        payload = ChargeDetailSerializer(charge, context={"request": request}).data
        if data.get("send_whatsapp"):
            payload["whatsapp_url"] = build_whatsapp_url(charge)
            mark_whatsapp_opened(charge=charge, actor=request.user)
        return Response(payload, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="eligible-sessions")
    def eligible_appointments(self, request):
        user = request.user
        professional_id = request.query_params.get("professional")
        if user.is_admin_role or user.is_secretary:
            from django.contrib.auth import get_user_model
            from apps.patients.models import Patient

            therapist = get_user_model().objects.filter(
                pk=professional_id, role="therapist", is_active=True
            ).first()
            if not therapist and request.query_params.get("patient"):
                patient = Patient.objects.select_related("therapist").filter(
                    pk=request.query_params["patient"]
                ).first()
                therapist = patient.therapist if patient else None
            if not therapist:
                raise ValidationError({"professional": "Informe um profissional válido."})
        else:
            therapist = user

        queryset = eligible_sessions(
            therapist=therapist,
            patient_id=request.query_params.get("patient"),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
        )
        return Response(EligibleAppointmentSerializer(queryset, many=True).data)

    @action(detail=False, methods=["post"], url_path="generate-monthly")
    def generate_monthly(self, request):
        serializer = GenerateMonthlyChargesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        therapist = user
        professional_id = request.data.get("professional")
        if user.is_admin_role or user.is_secretary:
            from django.contrib.auth import get_user_model

            therapist = get_user_model().objects.filter(
                pk=professional_id, role="therapist", is_active=True
            ).first()
            if not therapist:
                raise ValidationError({"professional": "Informe um profissional válido."})
        generated, errors = _service_call(
            generate_monthly_charges,
            therapist=therapist,
            actor=user,
            **serializer.validated_data,
        )
        return Response(
            {
                "generated_count": len(generated),
                "charge_ids": [item.pk for item in generated],
                "errors": errors,
            },
            status=status.HTTP_201_CREATED if generated else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="whatsapp")
    def whatsapp(self, request, pk=None):
        charge = self.get_object()
        url = _service_call(build_whatsapp_url, charge=charge)
        mark_whatsapp_opened(charge=charge, actor=request.user)
        return Response({"url": url, "status": charge.whatsapp_status})


class MonthlySubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = MonthlySubscriptionSerializer
    permission_classes = [FinancialPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = MonthlySubscription.objects.select_related(
            "patient", "professional", "therapist"
        )
        if user.is_admin_role or user.is_secretary:
            professional_id = self.request.query_params.get("professional")
            if professional_id:
                queryset = queryset.filter(professional_id=professional_id)
        else:
            queryset = queryset.filter(therapist=user)
        requested_status = self.request.query_params.get("status")
        if requested_status and requested_status != "all":
            queryset = queryset.filter(status=requested_status)
        return queryset

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        professional = data["professional"]
        instance = _service_call(
            create_subscription,
            therapist=professional,
            actor=self.request.user,
            validated_data=data,
        )
        serializer.instance = instance

    def perform_update(self, serializer):
        serializer.save()

    def _change_status(self, request, target):
        instance = _service_call(
            change_subscription_status,
            subscription=self.get_object(),
            target_status=target,
            actor=request.user,
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        return self._change_status(request, MonthlySubscription.Status.PAUSED)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        return self._change_status(request, MonthlySubscription.Status.ACTIVE)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._change_status(request, MonthlySubscription.Status.CANCELLED)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        return self._change_status(request, MonthlySubscription.Status.ENDED)

    @action(detail=True, methods=["post"], url_path="generate-occurrences")
    def generate_occurrences(self, request, pk=None):
        result = _service_call(
            process_due_subscription,
            subscription=self.get_object(),
            actor=request.user,
        )
        return Response(result)
__ELO_0001__

