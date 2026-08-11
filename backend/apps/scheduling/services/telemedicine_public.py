from __future__ import annotations

from apps.scheduling.exceptions import (
    TelemedicineAccessDeniedError,
    TelemedicineProviderUnavailableError,
)
from apps.scheduling.integrations.telemedicine import (
    TelemedicineProviderError,
    get_telemedicine_provider,
)
from apps.scheduling.selectors.telemedicine import (
    get_telemedicine_invitation_by_token,
)


def leave_patient_telemedicine(*, raw_token: str, identity: str) -> None:
    invitation = get_telemedicine_invitation_by_token(raw_token=raw_token)
    if not invitation.is_valid:
        return
    expected_prefix = f"telemed:{invitation.room.public_id.hex}:patient:"
    if not identity.startswith(expected_prefix):
        raise TelemedicineAccessDeniedError(
            "O participante não pertence a este atendimento."
        )
    provider = get_telemedicine_provider()
    try:
        provider.remove_participant(
            room_name=invitation.room.provider_room_name,
            identity=identity,
        )
    except TelemedicineProviderError as exc:
        raise TelemedicineProviderUnavailableError(
            "Não foi possível encerrar a conexão neste momento."
        ) from exc
