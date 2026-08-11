"""Adapter técnico para conversão de HTML em PDF."""

from __future__ import annotations

import logging

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


def render_html_to_pdf(html_content: str, *, renderer_cls=HTML) -> bytes:
    """Converte HTML previamente sanitizado em bytes de PDF."""

    return renderer_cls(string=html_content).write_pdf()
