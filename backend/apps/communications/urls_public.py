from django.urls import path

from .views import PublicCommunicationActionView

urlpatterns = [
    path("actions/<str:token>/", PublicCommunicationActionView.as_view(), name="public-communication-action"),
    path("actions/<str:token>/<str:action>/", PublicCommunicationActionView.as_view(), name="public-communication-action-submit"),
]
