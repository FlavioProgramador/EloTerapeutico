from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    WorkingHoursDetailView,
    WorkingHoursListCreateView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    SafeTokenRefreshView,
)

urlpatterns = [
    # Autenticação
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path(
        "token/refresh/",
        SafeTokenRefreshView.as_view(),
        name="token-refresh"
    ),
    path(
        "password/change/",
        ChangePasswordView.as_view(),
        name="auth-change-password"
    ),
    path(
        "password/reset/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset"
    ),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm"
    ),
    # Perfil
    path("me/", MeView.as_view(), name="user-me"),
    # Horários de atendimento
    path(
        "working-hours/",
        WorkingHoursListCreateView.as_view(),
        name="working-hours-list"
    ),
    path(
        "working-hours/<int:pk>/",
        WorkingHoursDetailView.as_view(),
        name="working-hours-detail"
    ),
]
