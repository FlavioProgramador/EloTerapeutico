"""Visualizador seguro de consultas SQL para superusuários no Django Admin."""

import re
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


def _get_first_sql_keyword(query: str) -> str:
    """Extrai a primeira palavra-chave executável da query, ignorando comentários."""
    # 1. Remove comentários de bloco /* ... */
    query_clean = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)
    
    # 2. Divide em linhas e descarta comentários de linha --
    lines = query_clean.splitlines()
    clean_lines = []
    for line in lines:
        cleaned_line = re.sub(r"--.*$", "", line).strip()
        if cleaned_line:
            clean_lines.append(cleaned_line)
            
    # 3. Junta as linhas e pega a primeira palavra
    query_flat = " ".join(clean_lines).strip()
    match = re.match(r"^([a-zA-Z]+)", query_flat)
    if match:
        return match.group(1).upper()
    return ""


@user_passes_test(lambda u: u.is_authenticated and u.is_superuser)
def sql_explorer_view(request):
    """Executa consultas SQL de leitura e retorna em formato de tabela."""
    context = admin.site.each_context(request)
    context["title"] = "SQL Explorer"
    
    query = request.POST.get("sql", "").strip()
    context["query"] = query

    if request.method == "POST" and query:
        # Validação básica de segurança (somente leitura, pulando comentários)
        first_keyword = _get_first_sql_keyword(query)
        allowed_prefixes = ("SELECT", "WITH", "SHOW", "EXPLAIN", "DESCRIBE", "PRAGMA")
        
        if first_keyword not in allowed_prefixes:
            context["error"] = (
                "Ação bloqueada. Apenas comandos de leitura (SELECT, WITH, SHOW, EXPLAIN) "
                "são permitidos por questões de segurança e integridade dos dados."
            )
            return render(request, "admin/sql_explorer.html", context)

        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    context["columns"] = [col[0] for col in cursor.description]
                    context["rows"] = cursor.fetchall()
                else:
                    context["columns"] = ["Resultado"]
                    context["rows"] = [("Comando executado com sucesso (nenhum registro retornado).",)]
        except Exception as e:
            context["error"] = str(e)

    return render(request, "admin/sql_explorer.html", context)


@require_GET
def sql_schema_view(request):
    """Retorna tabelas e colunas do banco de dados para autocomplete.
    Apenas superusuários autenticados podem acessar.
    """
    if not (request.user.is_authenticated and request.user.is_superuser):
        return JsonResponse({"error": "Forbidden"}, status=403)

    schema = {}
    with connection.cursor() as cursor:
        # Busca todas as tabelas do banco
        tables = connection.introspection.table_names(cursor)
        for table in sorted(tables):
            try:
                columns = [
                    col.name
                    for col in connection.introspection.get_table_description(cursor, table)
                ]
                schema[table] = columns
            except Exception:
                schema[table] = []

    return JsonResponse({"schema": schema})
