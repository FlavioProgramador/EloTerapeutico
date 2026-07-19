"""Compatibilidade lazy para os services movidos para ``apps.scheduling``.

A resolução sob demanda evita ciclos durante o bootstrap do Django quando módulos
canônicos ainda atravessam um caminho histórico específico.
"""

from importlib import import_module

_EXPORTS = {
    "apply_bulk_recurrence_change": ("apps.scheduling.services.recurrences", "apply_bulk_recurrence_change"),
    "build_appointments_csv": ("apps.scheduling.services.exports", "build_appointments_csv"),
    "cancel_appointment_for_deletion": ("apps.scheduling.services.appointments", "cancel_appointment_for_deletion"),
    "cancel_appointment_reminder": ("apps.scheduling.services.telemedicine", "cancel_appointment_reminder"),
    "cancel_patient_package": ("apps.scheduling.services.package_sessions", "cancel_patient_package"),
    "create_appointment": ("apps.scheduling.services.appointments", "create_appointment"),
    "create_appointment_resources": ("apps.scheduling.services.resources", "create_appointment_resources"),
    "create_patient_package": ("apps.scheduling.services.packages", "create_patient_package"),
    "create_schedule_block": ("apps.scheduling.services.schedule_blocks", "create_schedule_block"),
    "end_recurrence": ("apps.scheduling.services.recurrences", "end_recurrence"),
    "generate_recurrence_appointments": ("apps.scheduling.services.recurrences", "generate_recurrence_appointments"),
    "open_telemedicine_room": ("apps.scheduling.services.telemedicine", "open_telemedicine_room"),
    "recurrence_dates": ("apps.scheduling.services.recurrences", "recurrence_dates"),
    "regenerate_telemedicine_links": ("apps.scheduling.services.telemedicine", "regenerate_telemedicine_links"),
    "release_package_session": ("apps.scheduling.services.packages", "release_package_session"),
    "remove_package_session": ("apps.scheduling.services.package_sessions", "remove_package_session"),
    "set_recurrence_status": ("apps.scheduling.services.recurrences", "set_recurrence_status"),
    "sync_package_session_status": ("apps.scheduling.services.packages", "sync_package_session_status"),
    "update_appointment": ("apps.scheduling.services.appointments", "update_appointment"),
    "update_appointment_status": ("apps.scheduling.services.appointments", "update_appointment_status"),
}


def __getattr__(name: str):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


__all__ = sorted(_EXPORTS)
