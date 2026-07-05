"""CRUD das mensalidades do profissional autenticado."""

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from ..models import MonthlySubscription
from .serializers import MonthlySubscriptionSerializer
from .views import FinancialPermission


class MonthlySubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = MonthlySubscriptionSerializer
    permission_classes = [FinancialPermission]

    def get_queryset(self):
        user = self.request.user
        if not user.is_therapist:
            return MonthlySubscription.objects.none()
        queryset = MonthlySubscription.objects.filter(therapist=user).select_related(
            "patient", "professional"
        )
        requested_status = self.request.query_params.get("status")
        if requested_status and requested_status != "all":
            queryset = queryset.filter(status=requested_status)
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_therapist:
            raise ValidationError("Somente profissionais podem criar mensalidades.")
        serializer.save(
            therapist=self.request.user,
            professional=self.request.user,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
