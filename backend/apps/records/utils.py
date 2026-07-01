import re
from django.utils.html import escape

def render_markdown_safely(text: str) -> str:
    """
    Sanitiza e converte Markdown básico (apenas negrito, itálico e listas) para HTML.
    Preve XSS escapando HTML bruto e aplicando uma allowlist restrita de tags.
    Sublinhados foram removidos conforme requisitos.
    """
    if not text:
        return ""
    
    # Escapa todo o conteúdo para neutralizar scripts e tags perigosas
    escaped = escape(text)
    
    lines = escaped.split("\n")
    rendered_lines = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        stripped = line.strip()
        # Lista não-ordenada: - item
        if stripped.startswith("- "):
            if not in_ul:
                if in_ol:
                    rendered_lines.append("</ol>")
                    in_ol = False
                rendered_lines.append("<ul>")
                in_ul = True
            item_content = stripped[2:]
            rendered_lines.append(f"<li>{item_content}</li>")
        # Lista ordenada: 1. item
        elif re.match(r"^\d+\.\s", stripped):
            match = re.match(r"^(\d+)\.\s(.*)", stripped)
            if not in_ol:
                if in_ul:
                    rendered_lines.append("</ul>")
                    in_ul = False
                rendered_lines.append("<ol>")
                in_ol = True
            item_content = match.group(2)
            rendered_lines.append(f"<li>{item_content}</li>")
        else:
            # Fecha listas abertas se encontrar um parágrafo normal
            if in_ul:
                rendered_lines.append("</ul>")
                in_ul = False
            if in_ol:
                rendered_lines.append("</ol>")
                in_ol = False
            
            if stripped:
                rendered_lines.append(f"<p>{stripped}</p>")
                
    if in_ul:
        rendered_lines.append("</ul>")
    if in_ol:
        rendered_lines.append("</ol>")
        
    html_content = "".join(rendered_lines)
    
    # Converte negrito: **texto**
    html_content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_content)
    # Converte itálico: *texto*
    html_content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html_content)
    
    return html_content


def safe_url_fetcher(url, timeout=10, ssl_context=None):
    """
    Buscador de recursos para o WeasyPrint que restringe qualquer requisição
    de rede externa (SSRF) ou acesso local não mapeado a arquivos privados.
    """
    raise ValueError(f"Acesso a recursos externos bloqueado por segurança: {url}")
