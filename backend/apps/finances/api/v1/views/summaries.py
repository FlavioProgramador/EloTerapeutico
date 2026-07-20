"""Endpoint de indicadores financeiros."""

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.api.v1.serializers import FinancialSummaryQuerySerializer
from apps.finances.selectors import financial_summary


class FinancialSummaryActionsMixin:
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        serializer = FinancialSummaryQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(
            financial_summary(
                user=request.user,
                start_date=serializer.validated_data["start_date"],
                end_date=serializer.validated_data["end_date"],
            )
        )
