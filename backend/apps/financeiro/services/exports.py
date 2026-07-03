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
    writer.writerow(
        [
            "ID",
            "Tipo",
            "Categoria",
            "Valor (R$)",
            "Forma de Pagamento",
            "Status",
            "Paciente",
            "Vencimento",
            "Pago em",
            "Descrição",
            "Criado em",
        ]
    )
    for transaction in queryset:
        writer.writerow(
            [
                transaction.id,
                transaction.get_transaction_type_display(),
                transaction.get_category_display(),
                f"{transaction.amount:.2f}".replace(".", ","),
                transaction.get_payment_method_display(),
                transaction.get_payment_status_display(),
                transaction.patient.full_name
                if transaction.patient
                else "Não associado",
                transaction.due_date.strftime("%d/%m/%Y")
                if transaction.due_date
                else "",
                transaction.paid_at.strftime("%d/%m/%Y %H:%M")
                if transaction.paid_at
                else "",
                _safe_csv_cell(transaction.description),
                transaction.created_at.strftime("%d/%m/%Y %H:%M"),
            ]
        )
    return output.getvalue()
