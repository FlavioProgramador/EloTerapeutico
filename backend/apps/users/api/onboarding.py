from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.users.models import WorkingHours

from .serializers import UserProfileSerializer, WorkingHoursSerializer


class OnboardingWorkingHoursSerializer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_active = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError(
                "O horário de início deve ser anterior ao horário de fim."
            )
        return attrs


class OnboardingSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)
    crp_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    clinic_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    professional_address = serializers.JSONField(required=False)
    default_session_duration = serializers.IntegerField(min_value=10, max_value=480, required=False)
    default_session_value = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
        required=False,
    )
    working_hours = OnboardingWorkingHoursSerializer(many=True, required=False)
    complete = serializers.BooleanField(default=True)
    skip_optional = serializers.BooleanField(default=False)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OnboardingSerializer

    def get(self, request):
        return Response(
            {
                "user": UserProfileSerializer(request.user).data,
                "clinic_name": request.user.clinic_name,
                "professional_address": request.user.professional_address,
                "onboarding_completed": request.user.onboarding_completed,
                "onboarding_completed_at": request.user.onboarding_completed_at,
                "working_hours": WorkingHoursSerializer(
                    request.user.working_hours.all(),
                    many=True,
                ).data,
            }
        )

    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user.__class__.objects.select_for_update().get(pk=request.user.pk)

        editable_fields = (
            "full_name",
            "specialty",
            "crp_number",
            "clinic_name",
            "phone",
            "professional_address",
            "default_session_duration",
            "default_session_value",
        )
        update_fields: list[str] = []
        for field in editable_fields:
            if field in data:
                setattr(user, field, data[field])
                update_fields.append(field)

        should_complete = bool(data.get("complete") or data.get("skip_optional"))
        if should_complete and user.onboarding_completed_at is None:
            user.onboarding_completed_at = timezone.now()
            update_fields.append("onboarding_completed_at")

        if update_fields:
            user.full_clean(exclude=["password", "last_login"])
            user.save(update_fields=[*dict.fromkeys(update_fields)])

        if "working_hours" in data:
            supplied_weekdays: set[int] = set()
            for item in data["working_hours"]:
                supplied_weekdays.add(item["weekday"])
                WorkingHours.objects.update_or_create(
                    therapist=user,
                    weekday=item["weekday"],
                    defaults={
                        "start_time": item["start_time"],
                        "end_time": item["end_time"],
                        "is_active": item["is_active"],
                    },
                )
            if supplied_weekdays:
                WorkingHours.objects.filter(therapist=user).exclude(
                    weekday__in=supplied_weekdays
                ).update(is_active=False)

        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.UPDATE,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
            content_object=user,
            object_repr="Configuração inicial da conta atualizada",
        )

        return Response(
            {
                "message": (
                    "Configuração inicial concluída."
                    if user.onboarding_completed
                    else "Configuração inicial salva para continuar depois."
                ),
                "user": UserProfileSerializer(user).data,
                "onboarding_completed": user.onboarding_completed,
                "next": "/dashboard" if user.onboarding_completed else "/onboarding",
            },
            status=status.HTTP_200_OK,
        )

    patch = post
