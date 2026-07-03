"""Endpoint de solicitação de redefinição de senha."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.password_reset import request_password_reset
from .serializers import PasswordResetRequestSerializer


@extend_schema(tags=["auth"])
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(email=serializer.validated_data["email"])
        return Response(
            {
                "message": (
                    "Se o e-mail estiver cadastrado, você receberá um "
                    "link para redefinir sua senha."
                )
            },
            status=status.HTTP_200_OK,
        )
