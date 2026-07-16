from django.urls import path

from apps.billing.registration import PlanRegistrationView

from .api.clinic_views import (
    ClinicContextView,
    ClinicInvitationAcceptView,
    ClinicInvitationCreateView,
    ClinicSwitchView,
)
from .api.onboarding import OnboardingView
from .api.views import (
    AuthSessionListView,
    AuthSessionRevokeView,
    ChangePasswordView,
    LoginView,
    LogoutAllView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    SafeTokenRefreshView,
    WorkingHoursDetailView,
    WorkingHoursListCreateView,
)

urlpatterns = [
    path("register/", PlanRegistrationView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("logout-all/", LogoutAllView.as_view(), name="auth-logout-all"),
    path("sessions/", AuthSessionListView.as_view(), name="auth-session-list"),
    path(
        "sessions/<uuid:public_id>/revoke/",
        AuthSessionRevokeView.as_view(),
        name="auth-session-revoke",
    ),
    path("clinics/", ClinicContextView.as_view(), name="clinic-context"),
    path("clinics/switch/", ClinicSwitchView.as_view(), name="clinic-switch"),
    path(
        "clinics/invitations/",
        ClinicInvitationCreateView.as_view(),
        name="clinic-invitation-create",
    ),
    path(
        "clinics/invitations/accept/",
        ClinicInvitationAcceptView.as_view(),
        name="clinic-invitation-accept",
    ),
    path(
        "token/refresh/",
        SafeTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "password/change/",
        ChangePasswordView.as_view(),
        name="auth-change-password",
    ),
    path(
        "password/reset/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("me/", MeView.as_view(), name="user-me"),
    path("onboarding/", OnboardingView.as_view(), name="user-onboarding"),
    path(
        "working-hours/",
        WorkingHoursListCreateView.as_view(),
        name="working-hours-list",
    ),
    path(
        "working-hours/<int:pk>/",
        WorkingHoursDetailView.as_view(),
        name="working-hours-detail",
    ),
]
