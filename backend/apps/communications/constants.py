from __future__ import annotations

ALLOWED_TEMPLATE_VARIABLES = frozenset(
    {
        "patient_name",
        "guardian_name",
        "therapist_name",
        "clinic_name",
        "appointment_date",
        "appointment_time",
        "appointment_duration",
        "appointment_location",
        "appointment_modality",
        "meeting_link",
        "confirmation_link",
        "cancellation_link",
        "reschedule_link",
        "form_name",
        "form_link",
        "form_due_date",
        "document_name",
        "document_link",
        "document_expiration_date",
        "payment_amount",
        "payment_due_date",
        "payment_status",
        "receipt_link",
        "package_remaining_sessions",
        "support_email",
    }
)

BLOCKED_CLINICAL_VARIABLES = frozenset(
    {
        "diagnosis",
        "diagnostico",
        "clinical_note",
        "evolution",
        "evolucao",
        "anamnesis",
        "anamnese",
        "medical_record",
        "prontuario",
        "medication",
        "medicacao",
        "complaint",
        "queixa",
    }
)

DEFAULT_OPERATIONAL_FOOTER = (
    "Esta mensagem é destinada a comunicações administrativas. "
    "Em caso de emergência, procure o serviço de emergência da sua região."
)

RETRY_DELAYS_SECONDS = (60, 300, 1800, 7200)
