from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    WorkingHoursDetailView,
    WorkingHoursListCreateView,
)

urlpatterns = [
    # Autenticação
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("password/change/", ChangePasswordView.as_view(), name="auth-change-password"),
    # Perfil
    path("me/", MeView.as_view(), name="user-me"),
    # Horários de atendimento
    path("working-hours/", WorkingHoursListCreateView.as_view(), name="working-hours-list"),
    path("working-hours/<int:pk>/", WorkingHoursDetailView.as_view(), name="working-hours-detail"),
]
