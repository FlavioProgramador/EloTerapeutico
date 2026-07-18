"""Adapter técnico para renderização de documentos em PDF."""

from __future__ import annotations

import html
import json
import logging

from apps.documents.models import GeneratedDocument
from apps.documents.services.placeholders import render_safe_markdown

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML
except (ImportError, OSError):
    logger.warning(
        "WeasyPrint could not import Pango/GObject libraries. Using dummy PDF fallback for documents."
    )

    class HTML:  # type: ignore[no-redef]
        """Fallback mínimo para ambientes sem as bibliotecas nativas do WeasyPrint."""

        def __init__(self, string=None, url_fetcher=None, **kwargs):
            self.string = string

        def write_pdf(self, target=None, **kwargs):
            dummy_pdf = (
                b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
                b"trailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
            )
            if target is None:
                return dummy_pdf
            if hasattr(target, "write"):
                target.write(dummy_pdf)
                return dummy_pdf
            with open(target, "wb") as file_handle:
                file_handle.write(dummy_pdf)
            return dummy_pdf


def build_document_html(document: GeneratedDocument) -> str:
    """Monta o HTML sanitizado utilizado pelo renderer de PDF."""

    context = json.loads(document.context_snapshot or "{}")
    header = (
        render_safe_markdown(document.template_header_snapshot, context)
        if document.template_header_snapshot
        else ""
    )
    footer = (
        render_safe_markdown(document.template_footer_snapshot, context)
        if document.template_footer_snapshot
        else ""
    )
    number = html.escape(document.document_number, quote=True)
    professional_name = html.escape(document.professional_name_snapshot, quote=True)
    registration = html.escape(document.professional_registration_snapshot, quote=True)
    signature = ""
    if document.include_professional_identification_snapshot:
        signature = (
            '<div class="signature"><div class="signature-line"></div>'
            f"<strong>{professional_name}</strong><br>{registration}</div>"
        )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
@page {{ size: A4; margin: 24mm 20mm 22mm; @bottom-center {{ content: "{number}"; font-size: 8pt; color: #64748b; }} }}
body {{ font-family: DejaVu Sans, sans-serif; color: #172033; font-size: 11pt; line-height: 1.55; }}
header {{ border-bottom: 1px solid #dbe4f0; margin-bottom: 24px; padding-bottom: 12px; color: #475569; }}
footer {{ border-top: 1px solid #dbe4f0; margin-top: 28px; padding-top: 12px; color: #64748b; font-size: 9pt; }}
h1 {{ font-size: 18pt; margin: 0 0 16px; }} h2 {{ font-size: 14pt; margin: 18px 0 8px; }} h3 {{ font-size: 12pt; margin: 14px 0 6px; }}
p {{ margin: 0 0 10px; }} li {{ margin-bottom: 5px; }} .page-break {{ page-break-before: always; }}
.signature {{ margin-top: 42px; text-align: center; }} .signature-line {{ border-top: 1px solid #334155; width: 280px; margin: 0 auto 8px; }}
.meta {{ color: #64748b; font-size: 9pt; margin-bottom: 20px; }}
</style>
</head>
<body>
<header>{header}</header>
<div class="meta">Documento {number}</div>
<main>{document.rendered_content}</main>
{signature}
<footer>{footer}</footer>
</body>
</html>"""


def render_document_pdf(document: GeneratedDocument) -> bytes:
    """Renderiza o PDF final sem alterar estado ou persistência do documento."""

    return HTML(string=build_document_html(document)).write_pdf()
