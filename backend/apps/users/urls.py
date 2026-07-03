from django.urls import path

from .api.password_reset_views import PasswordResetRequestView
from .api.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    RegisterView,
    SafeTokenRefreshView,
    WorkingHoursDetailView,
    WorkingHoursListCreateView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
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
