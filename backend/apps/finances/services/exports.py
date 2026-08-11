"""Geração segura de exportações financeiras."""

import csv
from io import StringIO


def _safe_csv_cell(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def transactions_csv(queryset) -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Tipo", "Categoria", "Valor (R$)", "Forma de Pagamento", "Status", "Paciente", "Vencimento", "Pago em", "Descrição", "Criado em"])
    for item in queryset:
        writer.writerow([
            item.id, item.get_transaction_type_display(), item.get_category_display(),
            f"{item.amount:.2f}".replace(".", ","), item.get_payment_method_display(),
            item.get_payment_status_display(), item.patient.full_name if item.patient else "Não associado",
            item.due_date.strftime("%d/%m/%Y") if item.due_date else "",
            item.paid_at.strftime("%d/%m/%Y %H:%M") if item.paid_at else "",
            _safe_csv_cell(item.description), item.created_at.strftime("%d/%m/%Y %H:%M"),
        ])
    return output.getvalue()
