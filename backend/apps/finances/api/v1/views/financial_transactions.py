"""ViewSet base de transações financeiras."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.integrations import AuditLogMixin
from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event, safe_resource_repr
from apps.finances.api.v1.filters import FinancialTransactionFilter
from apps.finances.api.v1.permissions import FinancesPermission
from apps.finances.api.v1.serializers import (
    MarkAsPaidSerializer,
    TransactionCreateUpdateSerializer,
    TransactionDetailSerializer,
    TransactionListSerializer,
)
from apps.finances.selectors import pending_transactions, transactions_accessible_to
from apps.finances.services import (
    create_financial_transaction,
    delete_financial_transaction,
    update_financial_transaction,
)


class FinancialTransactionViewSetBase(AuditLogMixin, viewsets.ModelViewSet):
    permission_classes = [FinancesPermission]
    filterset_class = FinancialTransactionFilter
    ordering_fields = ["created_at", "due_date", "amount", "payment_status"]

    def get_queryset(self):
        return transactions_accessible_to(self.request.user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TransactionCreateUpdateSerializer
        if self.action == "list":
            return TransactionListSerializer
        if self.action == "mark_as_paid":
            return MarkAsPaidSerializer
        return TransactionDetailSerializer

    def perform_create(self, serializer):
        serializer.instance = create_financial_transaction(
            actor=self.request.user, validated_data=serializer.validated_data
        )
        self._record_instance(AuditLog.Action.CREATE, serializer.instance, on_commit=True)

    def perform_update(self, serializer):
        serializer.instance = update_financial_transaction(
            actor=self.request.user,
            financial_transaction=serializer.instance,
            validated_data=serializer.validated_data,
        )
        self._record_instance(AuditLog.Action.UPDATE, serializer.instance, on_commit=True)

    def perform_destroy(self, instance):
        resource_label = instance._meta.label
        resource_id = instance.pk
        resource_repr = safe_resource_repr(instance)
        delete_financial_transaction(
            actor=self.request.user, financial_transaction=instance
        )
        record_audit_event(
            action=AuditLog.Action.DELETE,
            actor=self.request.user,
            resource_label=resource_label,
            resource_id=resource_id,
            resource_repr=resource_repr,
            request=self.request,
            source=f"drf:{self.__class__.__name__}",
            on_commit=True,
        )

    @action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request):
        queryset = pending_transactions(
            user=request.user, patient_id=request.query_params.get("patient")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(TransactionListSerializer(queryset, many=True).data)
