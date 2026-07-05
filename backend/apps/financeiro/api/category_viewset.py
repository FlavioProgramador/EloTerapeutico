"""CRUD das categorias financeiras customizadas."""

from rest_framework import viewsets

from ..models import FinancialCategory
from .serializers import FinancialCategorySerializer
from .views import FinancialPermission


class FinancialCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialCategorySerializer
    permission_classes = [FinancialPermission]
    pagination_class = None

    def get_queryset(self):
        return FinancialCategory.objects.filter(therapist=self.request.user)
