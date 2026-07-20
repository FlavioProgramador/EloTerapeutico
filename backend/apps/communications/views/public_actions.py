from __future__ import annotations

import hashlib

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import PublicCommunicationActionToken
from ..services import handle_public_action, public_action_context, submit_public_form
from .common import _rate_limit


class PublicCommunicationActionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def get(self, request, token, action=None):
        token_fingerprint = hashlib.sha256(token.encode()).hexdigest()[:16]
        _rate_limit(f"public-get:{token_fingerprint}", limit=20, window_seconds=300)
        if action == "document-download":
            action_token = PublicCommunicationActionToken.resolve(token)
            if action_token is None or action_token.purpose != PublicCommunicationActionToken.Purpose.DOCUMENT_ACCESS or action_token.document_id is None:
                return Response({"status": "invalid", "message": "Este link é inválido ou expirou."}, status=status.HTTP_404_NOT_FOUND)
            document = action_token.document
            if document.status != document.Status.COMPLETED or not document.pdf_file:
                return Response({"status": "invalid", "message": "Este documento não está disponível."}, status=status.HTTP_404_NOT_FOUND)
            try:
                file_handle = document.pdf_file.open("rb")
            except (FileNotFoundError, OSError):
                return Response({"status": "invalid", "message": "Este documento não está disponível."}, status=status.HTTP_404_NOT_FOUND)
            action_token.used_at = timezone.now()
            action_token.save(update_fields=["used_at"])
            response = FileResponse(file_handle, as_attachment=True, filename=f"documento-{document.public_id}.pdf", content_type="application/pdf")
            response["Cache-Control"] = "private, no-store"
            response["X-Content-Type-Options"] = "nosniff"
            return response
        payload = public_action_context(token)
        if payload is None:
            return Response({"status": "invalid", "message": "Este link é inválido ou expirou."}, status=status.HTTP_404_NOT_FOUND)
        if payload.get("purpose") == PublicCommunicationActionToken.Purpose.DOCUMENT_ACCESS:
            payload["download_url"] = f"/api/v1/public/communications/actions/{token}/document-download/"
        return Response(payload)

    def post(self, request, token, action):
        _rate_limit(f"public-post:{hashlib.sha256(token.encode()).hexdigest()[:16]}", limit=8, window_seconds=300)
        try:
            if action == "form-submit":
                answers = request.data.get("answers")
                if not isinstance(answers, dict):
                    raise DjangoValidationError("Respostas inválidas.")
                payload = submit_public_form(token, answers)
            else:
                payload = handle_public_action(token, action)
        except DjangoValidationError:
            return Response({"status": "invalid", "message": "Não foi possível concluir esta ação."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payload)
