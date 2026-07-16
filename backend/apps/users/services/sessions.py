"""Serviços de emissão, rotação e revogação de sessões autenticadas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import AuthSession, User

SESSION_CLAIM = "sid"
_MAX_USER_AGENT_LENGTH = 255


def _token_expiration(token: RefreshToken) -> datetime:
    return datetime.fromtimestamp(int(token["exp"]), tz=UTC)


def _request_user_agent(request: Any | None) -> str:
    if request is None:
        return ""
    headers = getattr(request, "headers", {})
    raw_value = str(headers.get("User-Agent", ""))
    return " ".join(raw_value.split())[:_MAX_USER_AGENT_LENGTH]


def _attach_session_claim(refresh: RefreshToken, session: AuthSession) -> None:
    refresh[SESSION_CLAIM] = str(session.public_id)


def _create_session_for_refresh(
    *,
    user: User,
    refresh: RefreshToken,
    request: Any | None,
) -> AuthSession:
    session = AuthSession.objects.create(
        user=user,
        refresh_jti=str(refresh["jti"]),
        user_agent=_request_user_agent(request),
        expires_at=_token_expiration(refresh),
    )
    _attach_session_claim(refresh, session)
    return session


def issue_token_pair(*, user: User, request: Any | None = None) -> dict[str, str]:
    """Emite um par JWT vinculado a uma sessão persistida e revogável."""

    refresh = RefreshToken.for_user(user)
    _create_session_for_refresh(user=user, refresh=refresh, request=request)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _locked_session_for_refresh(
    *,
    refresh: RefreshToken,
    user: User,
) -> AuthSession | None:
    session_id = refresh.get(SESSION_CLAIM)
    if not session_id:
        return None

    session = (
        AuthSession.objects.select_for_update()
        .filter(public_id=session_id, user=user)
        .first()
    )
    if session is None:
        raise TokenError("Sessão inválida ou revogada.")
    if not session.is_active:
        raise TokenError("Sessão inválida ou revogada.")
    if session.refresh_jti != str(refresh["jti"]):
        # Impede replay e resolve refresh simultâneo: somente o primeiro token
        # que obtiver o lock ainda terá o JTI corrente da sessão.
        raise TokenError("Sessão inválida ou revogada.")
    return session


@transaction.atomic
def rotate_refresh_token(
    *,
    refresh: RefreshToken,
    user: User,
    request: Any | None = None,
) -> dict[str, str]:
    """Rotaciona o refresh token sob lock e invalida imediatamente o anterior."""

    session = _locked_session_for_refresh(refresh=refresh, user=user)
    refresh.blacklist()

    new_refresh = RefreshToken.for_user(user)
    now = timezone.now()
    if session is None:
        session = _create_session_for_refresh(
            user=user,
            refresh=new_refresh,
            request=request,
        )
    else:
        _attach_session_claim(new_refresh, session)
        session.refresh_jti = str(new_refresh["jti"])
        session.expires_at = _token_expiration(new_refresh)
        session.last_seen_at = now
        current_user_agent = _request_user_agent(request)
        if current_user_agent:
            session.user_agent = current_user_agent
        session.save(
            update_fields=[
                "refresh_jti",
                "expires_at",
                "last_seen_at",
                "user_agent",
            ]
        )

    return {
        "access": str(new_refresh.access_token),
        "refresh": str(new_refresh),
    }


@transaction.atomic
def revoke_refresh_token(
    *,
    refresh: RefreshToken,
    user: User,
    reason: str = "logout",
) -> None:
    """Revoga o refresh atual e a sessão persistida correspondente."""

    session = _locked_session_for_refresh(refresh=refresh, user=user)
    refresh.blacklist()
    if session is None:
        return

    session.revoked_at = timezone.now()
    session.revoked_reason = reason[:80]
    session.save(update_fields=["revoked_at", "revoked_reason"])


@transaction.atomic
def revoke_all_user_sessions(*, user: User, reason: str) -> int:
    """Revoga todas as sessões e refresh tokens ainda válidos do usuário."""

    now = timezone.now()
    sessions = list(
        AuthSession.objects.select_for_update().filter(
            user=user,
            revoked_at__isnull=True,
        )
    )
    AuthSession.objects.filter(pk__in=[session.pk for session in sessions]).update(
        revoked_at=now,
        revoked_reason=reason[:80],
    )

    outstanding_tokens = OutstandingToken.objects.filter(
        user=user,
        expires_at__gt=now,
    )
    for outstanding in outstanding_tokens.iterator():
        BlacklistedToken.objects.get_or_create(token=outstanding)

    return len(sessions)


@transaction.atomic
def revoke_user_session(
    *,
    user: User,
    public_id,
    reason: str = "device_revoked",
) -> AuthSession:
    """Revoga uma sessão específica sem permitir acesso a sessões de outro usuário."""

    session = AuthSession.objects.select_for_update().get(
        user=user,
        public_id=public_id,
    )
    if session.revoked_at is not None:
        return session

    outstanding = OutstandingToken.objects.filter(
        user=user,
        jti=session.refresh_jti,
    ).first()
    if outstanding is not None:
        BlacklistedToken.objects.get_or_create(token=outstanding)

    session.revoked_at = timezone.now()
    session.revoked_reason = reason[:80]
    session.save(update_fields=["revoked_at", "revoked_reason"])
    return session


def active_sessions_for_user(*, user: User):
    now = timezone.now()
    return AuthSession.objects.filter(
        user=user,
        revoked_at__isnull=True,
        expires_at__gt=now,
    ).order_by("-last_seen_at")
