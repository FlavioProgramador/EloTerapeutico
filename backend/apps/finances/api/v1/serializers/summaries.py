"""Serializers de parâmetros de indicadores financeiros."""

from calendar import monthrange
from datetime import date

from django.utils import timezone
from rest_framework import serializers


class FinancialSummaryQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    year = serializers.IntegerField(required=False, min_value=2000, max_value=2200)
    month = serializers.IntegerField(required=False, min_value=1, max_value=12)

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if bool(start_date) != bool(end_date):
            raise serializers.ValidationError("Informe o período completo.")
        if not start_date:
            today = timezone.localdate()
            year = attrs.get("year", today.year)
            month = attrs.get("month", today.month)
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
        if start_date > end_date:
            raise serializers.ValidationError("Informe um período válido.")
        attrs["start_date"] = start_date
        attrs["end_date"] = end_date
        return attrs
