"""Exportações do domínio de scheduling."""

from __future__ import annotations

import csv
from io import StringIO

from django.utils import timezone


def build_appointments_csv(*, appointments) -> str:
    """Gera CSV UTF-8 preservando o contrato histórico de colunas."""

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Data",
            "Início",
            "Fim",
            "Paciente",
            "Profissional",
            "Modalidade",
            "Status",
            "Sala",
        ]
    )
    for item in appointments.iterator():
        local_start = timezone.localtime(item.start_time)
        local_end = timezone.localtime(item.end_time)
        writer.writerow(
            [
                local_start.strftime("%d/%m/%Y"),
                local_start.strftime("%H:%M"),
                local_end.strftime("%H:%M"),
                item.patient.display_name,
                item.therapist.full_name,
                item.get_modality_display(),
                item.get_status_display(),
                item.room.name if item.room else "Sem sala",
            ]
        )
    return buffer.getvalue()


__all__ = ["build_appointments_csv"]
