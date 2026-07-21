"""Rotas versionadas do domínio de organizações."""

from django.urls import path

from .views import (
    InvitationAcceptView,
    OrganizationActivateView,
    OrganizationContextView,
    OrganizationDetailView,
    OrganizationInvitationActionView,
    OrganizationInvitationsView,
    OrganizationListCreateView,
    OrganizationMemberDetailView,
    OrganizationMembersView,
    OrganizationOnboardingCompleteView,
    OrganizationOnboardingView,
    OrganizationSettingsView,
    ProfessionalProfileView,
)

app_name = "organizations"

urlpatterns = [
    path("", OrganizationListCreateView.as_view(), name="list-create"),
    path("context/", OrganizationContextView.as_view(), name="context"),
    path("<uuid:organization_id>/", OrganizationDetailView.as_view(), name="detail"),
    path(
        "<uuid:organization_id>/activate/",
        OrganizationActivateView.as_view(),
        name="activate",
    ),
    path(
        "<uuid:organization_id>/members/",
        OrganizationMembersView.as_view(),
        name="members",
    ),
    path(
        "<uuid:organization_id>/members/<uuid:membership_id>/",
        OrganizationMemberDetailView.as_view(),
        name="member-detail",
    ),
    path(
        "<uuid:organization_id>/invitations/",
        OrganizationInvitationsView.as_view(),
        name="invitations",
    ),
    path(
        "<uuid:organization_id>/invitations/<uuid:invitation_id>/<str:action>/",
        OrganizationInvitationActionView.as_view(),
        name="invitation-action",
    ),
    path(
        "<uuid:organization_id>/settings/",
        OrganizationSettingsView.as_view(),
        name="settings",
    ),
    path(
        "<uuid:organization_id>/professional-profile/",
        ProfessionalProfileView.as_view(),
        name="professional-profile",
    ),
    path(
        "<uuid:organization_id>/onboarding/",
        OrganizationOnboardingView.as_view(),
        name="onboarding",
    ),
    path(
        "<uuid:organization_id>/onboarding/complete/",
        OrganizationOnboardingCompleteView.as_view(),
        name="onboarding-complete",
    ),
    path(
        "invitations/accept/",
        InvitationAcceptView.as_view(),
        name="invitation-accept",
    ),
]
