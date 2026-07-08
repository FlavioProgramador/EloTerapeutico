from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User

from ..professional_serializers import PatientProfessionalOptionSerializer


class PatientFormActions:
    @action(detail=False, methods=["get"], url_path="professionals")
    def professionals(self, request):
        if request.user.is_therapist:
            queryset = User.objects.filter(pk=request.user.pk, is_active=True)
        else:
            queryset = User.objects.filter(
                role=User.Role.THERAPIST,
                is_active=True,
            ).order_by("full_name")
        return Response(PatientProfessionalOptionSerializer(queryset, many=True).data)
