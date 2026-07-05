"""Base CRUD e autorização do livro de transações financeiras."""

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .filters import FinancialTransactionFilter
from .serializers import (
    MarkAsPaidSerializer,
    TransactionCreateUpdateSerializer,
    TransactionDetailSerializer,
    TransactionListSerializer,
)


class FinancialPermission(IsAuthenticated):
    """Restringe o módulo ao profissional proprietário dos dados."""

    def has_permission(self, request, view):
        return bool(super().has_permission(request, view) and request.user.is_therapist)

    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "therapist_id", None)
        return owner_id == request.user.pk


class TransactionViewSet(viewsets.ModelViewSet):
    """CRUD base. Actions especializadas são compostas em transaction_viewset.py."""

    permission_classes = [FinancialPermission]
    filterset_class = FinancialTransactionFilter
    ordering_fields = ["created_at", "due_date", "amount", "payment_status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        from ..selectors.transactions import transactions_accessible_to

        return transactions_accessible_to(self.request.user)

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return TransactionCreateUpdateSerializer
        if self.action == "list":
            return TransactionListSerializer
        if self.action == "mark_as_paid":
            return MarkAsPaidSerializer
        return TransactionDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete: mantém histórico financeiro e trilha referencial."""
        instance.deleted_at = timezone.now()
        instance.updated_by = self.request.user
        instance.save(update_fields=["deleted_at", "updated_by", "updated_at"])
