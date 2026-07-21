from __future__ import annotations

from django.core.exceptions import ValidationError

from ..models import Communication, CommunicationPreference, CommunicationRecipient
from ..providers import InvalidRecipient
from .privacy import CommunicationBlocked, mask_email, mask_phone, normalize_phone


def get_or_create_preference(
    owner,
    patient,
    *,
    organization=None,
) -> CommunicationPreference:
    organization = organization or patient.organization
    if patient.organization_id != organization.pk:
        raise ValidationError("O paciente pertence a outra organização.")
    preference, _ = CommunicationPreference.objects.get_or_create(
        organization=organization,
        patient=patient,
        defaults={
            "owner": owner,
            "allow_email": bool(patient.email),
            "allow_whatsapp": bool(patient.whatsapp or patient.phone),
            "allow_reminders": patient.reminders_enabled,
            "consented_at": patient.consent_at,
            "consent_source": (
                "patient_registration" if patient.consent_terms_accepted else ""
            ),
        },
    )
    if preference.owner_id != owner.pk:
        preference.owner = owner
        preference.save(update_fields=["owner", "updated_at"])
    return preference


def _resolve_recipient(
    owner,
    patient,
    channel: str,
    recipient_type: str | None = None,
    controlled_destination: str | None = None,
    category: str = Communication.Category.OTHER,
):
    if channel == Communication.Channel.IN_APP:
        return {
            "recipient_type": CommunicationRecipient.RecipientType.USER,
            "name": owner.full_name,
            "destination": str(owner.pk),
            "destination_masked": owner.full_name,
            "patient": None,
        }
    if patient is None and controlled_destination:
        if channel == Communication.Channel.EMAIL:
            if controlled_destination.casefold() != (owner.email or "").casefold():
                raise ValidationError(
                    "O teste de e-mail só pode ser enviado ao próprio usuário."
                )
            destination = controlled_destination
            masked = mask_email(destination)
        elif channel in {
            Communication.Channel.WHATSAPP_MANUAL,
            Communication.Channel.WHATSAPP,
            Communication.Channel.SMS,
        }:
            owner_phone = normalize_phone(owner.phone)
            destination = normalize_phone(controlled_destination)
            if not owner_phone or destination != owner_phone:
                raise ValidationError(
                    "O teste deste canal só pode ser enviado ao próprio usuário."
                )
            masked = mask_phone(destination)
        else:
            raise ValidationError("Canal inválido para teste controlado.")
        return {
            "recipient_type": CommunicationRecipient.RecipientType.USER,
            "name": owner.full_name,
            "destination": destination,
            "destination_masked": masked,
            "patient": None,
        }
    if patient is None or patient.therapist_id != owner.pk:
        raise ValidationError("Paciente inválido para este usuário.")
    if not patient.is_active:
        raise CommunicationBlocked("Paciente inativo não pode receber comunicações.")

    preference = get_or_create_preference(owner, patient)
    if preference.general_opt_out:
        raise CommunicationBlocked("O paciente optou por não receber comunicações.")
    if category in {
        Communication.Category.APPOINTMENT_CONFIRMATION,
        Communication.Category.APPOINTMENT_REMINDER,
        Communication.Category.APPOINTMENT_RESCHEDULED,
        Communication.Category.APPOINTMENT_CANCELED,
    } and not preference.allow_reminders:
        raise CommunicationBlocked("O paciente não permite lembretes de consultas.")
    if category in {
        Communication.Category.PAYMENT_DUE,
        Communication.Category.PAYMENT_OVERDUE,
        Communication.Category.PAYMENT_CONFIRMED,
        Communication.Category.PACKAGE_ENDING,
    } and not preference.allow_financial_notices:
        raise CommunicationBlocked("O paciente não permite avisos financeiros.")
    if category in {
        Communication.Category.FORM_REQUEST,
        Communication.Category.FORM_REMINDER,
    } and not preference.allow_form_requests:
        raise CommunicationBlocked(
            "O paciente não permite solicitações de formulários."
        )

    use_guardian = (
        recipient_type == CommunicationRecipient.RecipientType.GUARDIAN
        or preference.send_to_guardian
    )
    name = patient.guardian_name if use_guardian else patient.full_name
    if channel == Communication.Channel.EMAIL:
        if not preference.allow_email:
            raise CommunicationBlocked(
                "O paciente não permite comunicações por e-mail."
            )
        destination = patient.guardian_email if use_guardian else patient.email
        if not destination:
            raise InvalidRecipient("Este paciente não possui um e-mail válido.")
        masked = mask_email(destination)
    elif channel in {
        Communication.Channel.WHATSAPP_MANUAL,
        Communication.Channel.WHATSAPP,
        Communication.Channel.SMS,
    }:
        if channel == Communication.Channel.SMS and not preference.allow_sms:
            raise CommunicationBlocked("O paciente não permite comunicações por SMS.")
        if channel != Communication.Channel.SMS and not preference.allow_whatsapp:
            raise CommunicationBlocked(
                "O paciente não permite comunicações por WhatsApp."
            )
        raw = (
            patient.guardian_phone
            if use_guardian
            else (patient.whatsapp or patient.phone)
        )
        destination = normalize_phone(raw)
        masked = mask_phone(destination)
    else:
        raise ValidationError("Canal inválido.")

    return {
        "recipient_type": (
            CommunicationRecipient.RecipientType.GUARDIAN
            if use_guardian
            else CommunicationRecipient.RecipientType.PATIENT
        ),
        "name": name or "Destinatário",
        "destination": destination,
        "destination_masked": masked,
        "patient": patient,
    }
