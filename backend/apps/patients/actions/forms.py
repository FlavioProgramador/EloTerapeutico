from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.organizations.services.tenant_context import ensure_request_organization
from apps.patients.api.serializers.professional_serializers import PatientProfessionalOptionSerializer
from apps.users.models import User


class PatientFormActions:
    @action(detail=False, methods=["get"], url_path="professionals")
    def professionals(self, request):
        if request.user.is_therapist:
            queryset = User.objects.filter(pk=request.user.pk, is_active=True)
        else:
            organization, _ = ensure_request_organization(
                request=request,
                required=False,
            )
            if organization is not None:
                member_user_ids = OrganizationMembership.objects.filter(
                    organization=organization,
                    status=OrganizationMembership.Status.ACTIVE,
                    role__in=[
                        OrganizationMembership.Role.OWNER,
                        OrganizationMembership.Role.ADMIN,
                        OrganizationMembership.Role.THERAPIST,
                    ],
                ).values_list("user_id", flat=True)
                queryset = User.objects.filter(
                    pk__in=member_user_ids,
                    role=User.Role.THERAPIST,
                    is_active=True,
                ).order_by("full_name")
            else:
                queryset = User.objects.none()
        return Response(PatientProfessionalOptionSerializer(queryset, many=True).data)
