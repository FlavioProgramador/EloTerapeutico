from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from ..constants import DEFAULT_OPERATIONAL_FOOTER
from ..validators import plain_text_to_safe_html, render_template_text
from .privacy import _safe_variables


def build_default_variables(owner, patient=None, appointment=None) -> dict[str, str]:
    variables = {
        "therapist_name": owner.full_name,
        "clinic_name": owner.clinic_name or "Elo Terapêutico",
        "support_email": getattr(settings, "COMMUNICATIONS_REPLY_TO", "") or settings.DEFAULT_FROM_EMAIL,
    }
    if patient is not None:
        variables.update({"patient_name": patient.social_name or patient.full_name, "guardian_name": patient.guardian_name})
    if appointment is not None:
        local_start = timezone.localtime(appointment.start_time)
        variables.update(
            {
                "appointment_date": local_start.strftime("%d/%m/%Y"),
                "appointment_time": local_start.strftime("%H:%M"),
                "appointment_duration": str(appointment.duration_minutes),
                "appointment_location": appointment.get_modality_display(),
                "appointment_modality": appointment.get_modality_display(),
            }
        )
    return variables


def render_communication(template, variables: dict[str, object], *, append_footer: bool = True):
    safe_variables = _safe_variables(variables)
    subject = render_template_text(template.subject_template, safe_variables)
    body = render_template_text(template.body_template, safe_variables)
    if append_footer and DEFAULT_OPERATIONAL_FOOTER not in body:
        body = f"{body.rstrip()}\n\n{DEFAULT_OPERATIONAL_FOOTER}"
    return subject, body, plain_text_to_safe_html(body), safe_variables
