"""Validação defensiva de uploads do prontuário clínico."""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError

DEFAULT_MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_DOCX_ENTRIES = 1000

_ALLOWED_MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _read_prefix(uploaded_file, length: int = 32) -> bytes:
    position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    uploaded_file.seek(0)
    prefix = uploaded_file.read(length)
    uploaded_file.seek(position)
    return prefix


def _validate_signature(extension: str, prefix: bytes) -> None:
    valid = {
        ".pdf": prefix.startswith(b"%PDF-"),
        ".jpg": prefix.startswith(b"\xff\xd8\xff"),
        ".jpeg": prefix.startswith(b"\xff\xd8\xff"),
        ".png": prefix.startswith(b"\x89PNG\r\n\x1a\n"),
        ".docx": prefix.startswith(b"PK\x03\x04"),
    }
    if extension in valid and not valid[extension]:
        raise ValidationError("A assinatura real do arquivo não corresponde ao formato informado.")


def _validate_plain_text(uploaded_file) -> None:
    position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    uploaded_file.seek(0)
    content = uploaded_file.read()
    uploaded_file.seek(position)

    if b"\x00" in content:
        raise ValidationError("O arquivo de texto contém dados binários não permitidos.")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError("O arquivo de texto deve utilizar codificação UTF-8.") from exc


def _validate_docx(uploaded_file) -> None:
    position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    uploaded_file.seek(0)
    try:
        with zipfile.ZipFile(uploaded_file) as archive:
            entries = archive.infolist()
            max_entries = int(getattr(settings, "CLINICAL_DOCX_MAX_ENTRIES", DEFAULT_MAX_DOCX_ENTRIES))
            if len(entries) > max_entries:
                raise ValidationError("O documento possui uma quantidade excessiva de arquivos internos.")

            max_uncompressed = int(
                getattr(
                    settings,
                    "CLINICAL_DOCX_MAX_UNCOMPRESSED_BYTES",
                    DEFAULT_MAX_DOCX_UNCOMPRESSED_BYTES,
                )
            )
            total_uncompressed = sum(entry.file_size for entry in entries)
            if total_uncompressed > max_uncompressed:
                raise ValidationError("O conteúdo descompactado do documento excede o limite permitido.")

            names = {entry.filename for entry in entries}
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ValidationError("O arquivo não possui uma estrutura DOCX válida.")

            for entry in entries:
                path = PurePosixPath(entry.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise ValidationError("O documento contém caminhos internos inseguros.")
                if entry.flag_bits & 0x1:
                    raise ValidationError("Documentos DOCX protegidos por senha não são permitidos.")
    except zipfile.BadZipFile as exc:
        raise ValidationError("O arquivo DOCX está corrompido ou possui formato inválido.") from exc
    finally:
        uploaded_file.seek(position)


def validate_clinical_document_upload(uploaded_file):
    """Valida tamanho, extensão, MIME declarado e conteúdo estrutural."""

    max_bytes = int(getattr(settings, "CLINICAL_DOCUMENT_MAX_BYTES", DEFAULT_MAX_DOCUMENT_BYTES))
    if uploaded_file.size <= 0:
        raise ValidationError("O arquivo está vazio.")
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"O arquivo deve possuir no máximo {max_bytes // (1024 * 1024)} MB.")

    extension = Path(str(uploaded_file.name or "")).suffix.lower()
    expected_mime = _ALLOWED_MIME_BY_EXTENSION.get(extension)
    if not expected_mime:
        raise ValidationError("Extensão de arquivo não permitida.")

    declared_mime = str(getattr(uploaded_file, "content_type", "") or "").split(";", 1)[0].strip().lower()
    if declared_mime != expected_mime:
        raise ValidationError("O tipo MIME declarado não corresponde à extensão do arquivo.")

    prefix = _read_prefix(uploaded_file)
    _validate_signature(extension, prefix)
    if extension == ".txt":
        _validate_plain_text(uploaded_file)
    elif extension == ".docx":
        _validate_docx(uploaded_file)

    uploaded_file.seek(0)
    return uploaded_file
