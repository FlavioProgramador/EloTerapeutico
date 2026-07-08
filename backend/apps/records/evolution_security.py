"""Regras de segurança compartilhadas pelo fluxo de evoluções clínicas."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

DEFAULT_MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_ATTACHMENTS = 10
DEFAULT_MAX_CONTENT_LENGTH = 50_000

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
_ALLOWED_MIME_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}
_DANGEROUS_HTML = re.compile(
    r"<(?:script|iframe|object|embed|style|link|meta|svg)\b[^>]*>.*?</(?:script|iframe|object|embed|style|svg)>|"
    r"<(?:script|iframe|object|embed|style|link|meta|svg)\b[^>]*/?>",
    flags=re.IGNORECASE | re.DOTALL,
)
_ANY_HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
_DANGEROUS_SCHEME = re.compile(r"(?:javascript|vbscript|data)\s*:", flags=re.IGNORECASE)
_EVENT_HANDLER = re.compile(r"\bon[a-z]+\s*=", flags=re.IGNORECASE)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SAFE_FILENAME_CHARS = re.compile(r"[^\w.()\- ]+", flags=re.UNICODE)


def sanitize_clinical_markdown(value: str | None) -> str:
    """Normaliza Markdown e remove HTML ou protocolos executáveis.

    O conteúdo permanece texto Markdown. A renderização continua responsável por
    escapar o texto antes de gerar HTML, oferecendo defesa em profundidade.
    """

    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)
    text = _DANGEROUS_HTML.sub("", text)
    text = _ANY_HTML_TAG.sub("", text)
    text = _DANGEROUS_SCHEME.sub("", text)
    text = _EVENT_HANDLER.sub("", text)
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip()

    max_length = int(getattr(settings, "CLINICAL_EVOLUTION_MAX_CONTENT_LENGTH", DEFAULT_MAX_CONTENT_LENGTH))
    if len(text) > max_length:
        raise ValidationError(f"O conteúdo da evolução deve possuir no máximo {max_length} caracteres.")
    return text


def sanitize_original_filename(filename: str) -> str:
    """Retorna somente um nome de exibição seguro, sem alterar o nome físico UUID."""

    basename = Path(str(filename or "arquivo")).name
    basename = unicodedata.normalize("NFKC", basename)
    basename = _CONTROL_CHARS.sub("", basename)
    basename = _SAFE_FILENAME_CHARS.sub("_", basename).strip(" .")
    if not basename:
        basename = "arquivo"
    return basename[:255]


def _detect_mime(header: bytes) -> str | None:
    if header.startswith(b"%PDF-"):
        return "application/pdf"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_clinical_upload(uploaded_file):
    """Valida tamanho, extensão, MIME declarado e assinatura real do arquivo."""

    max_bytes = int(getattr(settings, "CLINICAL_ATTACHMENT_MAX_BYTES", DEFAULT_MAX_ATTACHMENT_BYTES))
    if uploaded_file.size <= 0:
        raise ValidationError("O arquivo está vazio.")
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"O arquivo deve possuir no máximo {max_bytes // (1024 * 1024)} MB.")

    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise ValidationError("Extensão de arquivo não permitida.")

    expected_mime = _ALLOWED_MIME_BY_EXTENSION[extension]
    declared_mime = (getattr(uploaded_file, "content_type", "") or "").lower()
    if declared_mime != expected_mime:
        raise ValidationError("O tipo MIME declarado não corresponde à extensão.")

    header = uploaded_file.read(16)
    uploaded_file.seek(0)
    detected_mime = _detect_mime(header)
    if detected_mime != expected_mime:
        raise ValidationError("A assinatura real do arquivo é inválida ou não permitida.")
    return uploaded_file


def max_evolution_attachments() -> int:
    return max(
        1,
        int(
            getattr(
                settings,
                "CLINICAL_EVOLUTION_MAX_ATTACHMENTS",
                DEFAULT_MAX_ATTACHMENTS,
            )
        ),
    )


def validate_session_date(session_date: date, user) -> date:
    """Impede datas futuras e restringe lançamentos retroativos sensíveis."""

    today = timezone.localdate()
    if session_date > today:
        raise ValidationError("A data do atendimento não pode estar no futuro.")

    retroactive_days = int(getattr(settings, "CLINICAL_RETROACTIVE_WINDOW_DAYS", 7))
    is_old = session_date < today - timedelta(days=retroactive_days)
    can_retroact = bool(
        getattr(user, "is_superuser", False)
        or getattr(user, "is_admin_role", False)
        or user.has_perm("records.add_retroactive_evolution")
    )
    if is_old and not can_retroact:
        raise ValidationError("Evoluções retroativas além do prazo permitido exigem autorização.")
    return session_date


def can_view_confidential_evolution(user, evolution) -> bool:
    if not evolution.is_confidential:
        return True
    return bool(
        user
        and user.is_authenticated
        and (
            evolution.created_by_id == user.id
            or getattr(user, "is_superuser", False)
            or user.has_perm("records.view_confidential_evolution")
        )
    )
