"""Casos de uso públicos do domínio de scheduling."""

from .appointments import (
    cancel_appointment_for_deletion,
    create_appointment,
    update_appointment,
    update_appointment_status,
)
from .exports import build_appointments_csv
from .package_sessions import cancel_patient_package, remove_package_session
from .packages import (
    create_patient_package,
    release_package_session,
    sync_package_session_status,
)
from .recurrences import (
    apply_bulk_recurrence_change,
    end_recurrence,
    generate_recurrence_appointments,
    recurrence_dates,
    set_recurrence_status,
)
from .resources import create_appointment_resources
from .schedule_blocks import create_schedule_block
from .telemedicine import (
    cancel_appointment_reminder,
    create_patient_invitation,
    exchange_patient_invitation,
    expire_telemedicine_rooms,
    finish_telemedicine_room,
    issue_patient_join_credentials,
    issue_professional_join_credentials,
    open_telemedicine_room,
    process_telemedicine_webhook,
    record_telemedicine_consent,
    regenerate_telemedicine_links,
    remove_telemedicine_participant,
    revoke_patient_invitation,
)

__all__ = [
    "apply_bulk_recurrence_change",
    "build_appointments_csv",
    "cancel_appointment_for_deletion",
    "cancel_appointment_reminder",
    "cancel_patient_package",
    "create_appointment",
    "create_appointment_resources",
    "create_patient_invitation",
    "create_patient_package",
    "create_schedule_block",
    "end_recurrence",
    "exchange_patient_invitation",
    "expire_telemedicine_rooms",
    "finish_telemedicine_room",
    "generate_recurrence_appointments",
    "issue_patient_join_credentials",
    "issue_professional_join_credentials",
    "open_telemedicine_room",
    "process_telemedicine_webhook",
    "record_telemedicine_consent",
    "recurrence_dates",
    "regenerate_telemedicine_links",
    "release_package_session",
    "remove_package_session",
    "remove_telemedicine_participant",
    "revoke_patient_invitation",
    "set_recurrence_status",
    "sync_package_session_status",
    "update_appointment",
    "update_appointment_status",
]
