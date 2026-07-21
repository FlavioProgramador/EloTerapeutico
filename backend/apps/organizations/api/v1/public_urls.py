from django.urls import path

from .views import InvitationAcceptView

urlpatterns = [path("", InvitationAcceptView.as_view(), name="organization-invitation-accept")]
