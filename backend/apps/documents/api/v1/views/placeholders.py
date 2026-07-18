"""View de placeholders documentais disponíveis."""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.services.placeholders import list_placeholders

from ..permissions import IsClinicalDocumentUser


class PlaceholderListView(APIView):
    permission_classes = [IsClinicalDocumentUser]

    def get(self, request):
        return Response(list_placeholders())
