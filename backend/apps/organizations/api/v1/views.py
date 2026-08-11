"""Views da API v1 de organizações, equipe e onboarding."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization, OrganizationInvitation
from apps.organizations.permissions import require_capability
from apps.organizations.selectors import (
    get_active_membership,
    get_invitation,
    get_membership,
    get_onboarding_context,
    get_visible_organization,
    list_invitations,
    list_memberships,
    list_user_organizations,
)
from apps.organizations.services import (
    accept_invitation,
    activate_organization,
    complete_onboarding,
    create_invitation,
    create_organization,
    remove_membership,
    resend_invitation,
    revoke_invitation,
    update_membership,
    update_onboarding,
    update_organization,
)
from apps.organizations.services.member_creation import add_existing_member

from .serializers import (
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MembershipCreateSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    OnboardingCompleteSerializer,
    OnboardingUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    OrganizationSettingsSerializer,
    ProfessionalProfileSerializer,
)


def _get_context(request, organization_id):
    try:
        organization = get_visible_organization(
            user=request.user,
            organization_id=organization_id,
        )
        membership = get_active_membership(
            organization=organization,
            user=request.user,
        )
    except ObjectDoesNotExist as exc:
        raise NotFound("Organização não encontrada.") from exc
    return organization, membership


class OrganizationListCreateView(APIView):
    def get(self, request):
        organizations = list_user_organizations(user=request.user)
        return Response(OrganizationSerializer(organizations, many=True).data)

    def post(self, request):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = create_organization(
            actor=request.user,
            data=serializer.validated_data,
            request=request,
        )
        return Response(
            OrganizationSerializer(organization).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationContextView(APIView):
    def get(self, request):
        organizations = list_user_organizations(user=request.user)
        membership = getattr(request, "organization_membership", None)
        return Response(
            {
                "active_organization": OrganizationSerializer(
                    getattr(request, "organization", None)
                ).data
                if getattr(request, "organization", None)
                else None,
                "active_membership": MembershipSerializer(membership).data
                if membership
                else None,
                "organizations": OrganizationSerializer(organizations, many=True).data,
            }
        )


class OrganizationDetailView(APIView):
    def get(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.view")
        return Response(OrganizationSerializer(organization).data)

    def patch(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.update")
        serializer = OrganizationCreateSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        organization = update_organization(
            actor=request.user,
            organization=organization,
            data=serializer.validated_data,
            request=request,
        )
        return Response(OrganizationSerializer(organization).data)


class OrganizationActivateView(APIView):
    def post(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.view")
        active_membership = activate_organization(
            actor=request.user,
            organization=organization,
        )
        return Response(
            {
                "organization": OrganizationSerializer(organization).data,
                "membership": MembershipSerializer(active_membership).data,
            }
        )


class OrganizationMembersView(APIView):
    def get(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_members")
        return Response(
            MembershipSerializer(
                list_memberships(organization=organization),
                many=True,
            ).data
        )

    def post(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_members")
        serializer = MembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data["role"]
        if role == "owner" and membership.role != "owner":
            raise ValidationError("Somente um proprietário pode adicionar outro proprietário.")
        try:
            created = add_existing_member(
                actor=request.user,
                organization=organization,
                request=request,
                **serializer.validated_data,
            )
        except ObjectDoesNotExist as exc:
            raise NotFound("Usuário não encontrado. Utilize um convite por e-mail.") from exc
        return Response(
            MembershipSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationMemberDetailView(APIView):
    def get(self, request, organization_id, membership_id):
        organization, actor_membership = _get_context(request, organization_id)
        require_capability(actor_membership, "organization.manage_members")
        try:
            membership = get_membership(
                organization=organization,
                membership_id=membership_id,
            )
        except ObjectDoesNotExist as exc:
            raise NotFound("Membro não encontrado.") from exc
        return Response(MembershipSerializer(membership).data)

    def patch(self, request, organization_id, membership_id):
        organization, actor_membership = _get_context(request, organization_id)
        require_capability(actor_membership, "organization.manage_members")
        membership = get_membership(
            organization=organization,
            membership_id=membership_id,
        )
        serializer = MembershipUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("role") == "owner" and actor_membership.role != "owner":
            raise ValidationError("Somente um proprietário pode promover outro proprietário.")
        updated = update_membership(
            actor=request.user,
            membership=membership,
            data=serializer.validated_data,
            request=request,
        )
        return Response(MembershipSerializer(updated).data)

    def delete(self, request, organization_id, membership_id):
        organization, actor_membership = _get_context(request, organization_id)
        require_capability(actor_membership, "organization.manage_members")
        membership = get_membership(
            organization=organization,
            membership_id=membership_id,
        )
        remove_membership(
            actor=request.user,
            membership=membership,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationInvitationsView(APIView):
    def get(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_invitations")
        return Response(
            InvitationSerializer(
                list_invitations(organization=organization),
                many=True,
            ).data
        )

    def post(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_invitations")
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, _ = create_invitation(
            actor=request.user,
            organization=organization,
            request=request,
            **serializer.validated_data,
        )
        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationInvitationActionView(APIView):
    def post(self, request, organization_id, invitation_id, action):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_invitations")
        try:
            invitation = get_invitation(
                organization=organization,
                invitation_id=invitation_id,
            )
        except OrganizationInvitation.DoesNotExist as exc:
            raise NotFound("Convite não encontrado.") from exc
        if action == "resend":
            invitation, _ = resend_invitation(
                actor=request.user,
                invitation=invitation,
                request=request,
            )
        elif action == "revoke":
            invitation = revoke_invitation(
                actor=request.user,
                invitation=invitation,
                request=request,
            )
        else:
            raise NotFound("Ação não encontrada.")
        return Response(InvitationSerializer(invitation).data)


class InvitationAcceptView(APIView):
    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = accept_invitation(
            actor=request.user,
            raw_token=serializer.validated_data["token"],
            request=request,
        )
        return Response(MembershipSerializer(membership).data)


class OrganizationSettingsView(APIView):
    def get(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_settings")
        context = get_onboarding_context(
            organization=organization,
            user=request.user,
        )
        return Response(OrganizationSettingsSerializer(context["settings"]).data)

    def patch(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        require_capability(membership, "organization.manage_settings")
        serializer = OrganizationSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        result = update_onboarding(
            actor=request.user,
            organization=organization,
            membership=membership,
            data={"settings": serializer.validated_data},
            request=request,
        )
        return Response(OrganizationSettingsSerializer(result["settings"]).data)


class ProfessionalProfileView(APIView):
    def get(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        context = get_onboarding_context(
            organization=organization,
            user=request.user,
        )
        profile = context["professional_profile"]
        if profile is None:
            raise NotFound("Perfil profissional não configurado.")
        return Response(ProfessionalProfileSerializer(profile).data)

    def patch(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        serializer = ProfessionalProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        result = update_onboarding(
            actor=request.user,
            organization=organization,
            membership=membership,
            data={"professional_profile": serializer.validated_data},
            request=request,
        )
        return Response(
            ProfessionalProfileSerializer(result["professional_profile"]).data
        )


class OrganizationOnboardingView(APIView):
    def get(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        context = get_onboarding_context(
            organization=organization,
            user=request.user,
        )
        return Response(
            {
                "organization": OrganizationSerializer(context["organization"]).data,
                "membership": MembershipSerializer(context["membership"]).data,
                "settings": OrganizationSettingsSerializer(context["settings"]).data,
                "professional_profile": ProfessionalProfileSerializer(
                    context["professional_profile"]
                ).data
                if context["professional_profile"]
                else None,
                "status": context["status"],
                "step": context["step"],
                "completed_at": context["completed_at"],
            }
        )

    def patch(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        serializer = OnboardingUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_onboarding(
            actor=request.user,
            organization=organization,
            membership=membership,
            data=serializer.validated_data,
            request=request,
        )
        return self.get(request, organization_id)


class OrganizationOnboardingCompleteView(APIView):
    def post(self, request, organization_id):
        organization, membership = _get_context(request, organization_id)
        serializer = OnboardingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complete_onboarding(
            actor=request.user,
            organization=organization,
            membership=membership,
            request=request,
        )
        return Response(OrganizationSerializer(organization).data)
