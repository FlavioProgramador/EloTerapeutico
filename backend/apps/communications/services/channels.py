from __future__ import annotations

from copy import deepcopy
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import Communication, CommunicationChannelConfig
from ..providers import ProviderError, ProviderNotConfigured, get_provider


# Valor de metadado usado pelo schema dinâmico do frontend. Não representa
# credencial ou segredo hardcoded; evita falso positivo B105 do Bandit.
_SENSITIVE_FIELD = True


_PROVIDER_DEFINITIONS: dict[str, dict[str, Any]] = {
    Communication.Channel.IN_APP: {
        "default_provider": "in_app",
        "providers": [
            {
                "id": "in_app",
                "label": "Comunicação interna",
                "description": "Notificações exibidas dentro do Elo Terapêutico.",
                "instructions": "O canal interno não exige credenciais externas.",
                "fields": [
                    {"name": "desktop_enabled", "label": "Exibir no dashboard", "kind": "boolean", "required": False, "default": True},
                    {"name": "sound_enabled", "label": "Som de notificação", "kind": "boolean", "required": False, "default": False},
                    {"name": "duration_seconds", "label": "Duração do aviso (segundos)", "kind": "number", "required": False, "default": 8},
                ],
                "secret_fields": [],
            }
        ],
    },
    Communication.Channel.EMAIL: {
        "default_provider": "django_email",
        "providers": [
            {
                "id": "django_email",
                "label": "Backend padrão do Django",
                "description": "Usa o backend de e-mail definido nas variáveis de ambiente do servidor.",
                "instructions": "Configure EMAIL_BACKEND, DEFAULT_FROM_EMAIL e as variáveis SMTP no ambiente de produção.",
                "fields": [
                    {"name": "sender_name", "label": "Nome do remetente", "kind": "text", "required": False},
                    {"name": "sender_email", "label": "E-mail do remetente", "kind": "email", "required": False},
                    {"name": "reply_to", "label": "E-mail de resposta", "kind": "email", "required": False},
                    {"name": "signature", "label": "Assinatura padrão", "kind": "textarea", "required": False},
                    {"name": "tracking_enabled", "label": "Rastreamento de entrega", "kind": "boolean", "required": False, "default": False},
                ],
                "secret_fields": [],
            },
            {
                "id": "smtp",
                "label": "SMTP personalizado",
                "description": "Conecta diretamente a um servidor SMTP específico deste terapeuta.",
                "instructions": "Use uma senha de aplicativo quando o provedor exigir autenticação em duas etapas. TLS e SSL não podem ser ativados simultaneamente.",
                "fields": [
                    {"name": "host", "label": "Servidor SMTP", "kind": "text", "required": True, "placeholder": "smtp.exemplo.com"},
                    {"name": "port", "label": "Porta", "kind": "number", "required": True, "default": 587},
                    {"name": "username", "label": "Usuário", "kind": "text", "required": True, "secret": _SENSITIVE_FIELD},
                    {"name": "password", "label": "Senha", "kind": "password", "required": True, "secret": _SENSITIVE_FIELD},
                    {"name": "use_tls", "label": "Usar TLS", "kind": "boolean", "required": False, "default": True},
                    {"name": "use_ssl", "label": "Usar SSL", "kind": "boolean", "required": False, "default": False},
                    {"name": "timeout", "label": "Timeout (segundos)", "kind": "number", "required": False, "default": 15},
                    {"name": "sender_name", "label": "Nome do remetente", "kind": "text", "required": True},
                    {"name": "sender_email", "label": "E-mail do remetente", "kind": "email", "required": True},
                    {"name": "reply_to", "label": "E-mail de resposta", "kind": "email", "required": False},
                    {"name": "signature", "label": "Assinatura padrão", "kind": "textarea", "required": False},
                ],
                "secret_fields": ["username", "password"],
            },
        ],
    },
    Communication.Channel.WHATSAPP_MANUAL: {
        "default_provider": "whatsapp_manual",
        "providers": [
            {
                "id": "whatsapp_manual",
                "label": "Link oficial do WhatsApp",
                "description": "Gera um link wa.me e exige confirmação humana do envio.",
                "instructions": "O Elo Terapêutico nunca marca mensagens manuais como entregues ou lidas.",
                "fields": [
                    {"name": "open_in_web", "label": "Preferir WhatsApp Web", "kind": "boolean", "required": False, "default": True},
                    {"name": "country_code", "label": "Código do país padrão", "kind": "text", "required": False, "default": "55"},
                ],
                "secret_fields": [],
            }
        ],
    },
    Communication.Channel.WHATSAPP: {
        "default_provider": "",
        "providers": [
            {
                "id": "meta_cloud",
                "label": "WhatsApp Cloud API (Meta)",
                "description": "Integração oficial com a API do WhatsApp Business da Meta.",
                "instructions": "Crie um aplicativo empresarial na Meta, vincule a conta do WhatsApp Business e informe o Phone Number ID e um token válido.",
                "fields": [
                    {"name": "business_account_id", "label": "ID da conta comercial", "kind": "text", "required": False},
                    {"name": "phone_number_id", "label": "Phone Number ID", "kind": "text", "required": True},
                    {"name": "phone_number", "label": "Número comercial", "kind": "tel", "required": True},
                    {"name": "api_version", "label": "Versão da Graph API", "kind": "text", "required": False, "default": "v23.0"},
                    {"name": "webhook_url", "label": "URL do webhook", "kind": "url", "required": False, "read_only": True},
                    {"name": "default_language", "label": "Idioma padrão dos templates", "kind": "text", "required": False, "default": "pt_BR"},
                    {"name": "access_token", "label": "Token de acesso", "kind": "password", "required": True, "secret": _SENSITIVE_FIELD},
                    {"name": "app_secret", "label": "Segredo do aplicativo", "kind": "password", "required": False, "secret": _SENSITIVE_FIELD},
                    {"name": "verify_token", "label": "Token de verificação do webhook", "kind": "password", "required": True, "secret": _SENSITIVE_FIELD},
                ],
                "secret_fields": ["access_token", "app_secret", "verify_token"],
            }
        ],
    },
    Communication.Channel.SMS: {
        "default_provider": "",
        "providers": [
            {
                "id": "twilio",
                "label": "Twilio SMS",
                "description": "Envio de SMS com rastreamento por meio da API oficial da Twilio.",
                "instructions": "Informe o Account SID, Auth Token e um número remetente habilitado para SMS.",
                "fields": [
                    {"name": "account_sid", "label": "Account SID", "kind": "text", "required": True},
                    {"name": "sender", "label": "Número remetente", "kind": "tel", "required": True},
                    {"name": "country_code", "label": "Código do país padrão", "kind": "text", "required": False, "default": "55"},
                    {"name": "monthly_limit", "label": "Limite mensal de mensagens", "kind": "number", "required": False},
                    {"name": "status_callback_url", "label": "URL de status", "kind": "url", "required": False, "read_only": True},
                    {"name": "auth_token", "label": "Auth Token", "kind": "password", "required": True, "secret": _SENSITIVE_FIELD},
                ],
                "secret_fields": ["auth_token"],
            }
        ],
    },
}


def _provider_definition(channel: str, provider: str) -> dict[str, Any]:
    channel_definition = _PROVIDER_DEFINITIONS.get(channel)
    if channel_definition is None:
        raise ValidationError("Canal de comunicação inválido.")
    for item in channel_definition["providers"]:
        if item["id"] == provider:
            return item
    raise ValidationError({"provider": "Provedor não suportado para este canal."})


def get_channel_catalog(channel: str | None = None) -> list[dict[str, Any]] | dict[str, Any]:
    if channel is None:
        return [
            {
                "channel": channel_name,
                "default_provider": definition["default_provider"],
                "providers": deepcopy(definition["providers"]),
            }
            for channel_name, definition in _PROVIDER_DEFINITIONS.items()
        ]
    definition = _PROVIDER_DEFINITIONS.get(channel)
    if definition is None:
        raise ValidationError("Canal de comunicação inválido.")
    return {
        "channel": channel,
        "default_provider": definition["default_provider"],
        "providers": deepcopy(definition["providers"]),
    }


def get_configured_secret_state(config: CommunicationChannelConfig) -> dict[str, bool]:
    if not config.provider:
        return {}
    definition = _provider_definition(config.channel, config.provider)
    credentials = config.get_credentials()
    return {field: bool(credentials.get(field)) for field in definition.get("secret_fields", [])}


def get_missing_configuration_fields(config: CommunicationChannelConfig) -> list[str]:
    if not config.provider:
        return ["provider"]
    definition = _provider_definition(config.channel, config.provider)
    credentials = config.get_credentials()
    missing: list[str] = []
    for field in definition.get("fields", []):
        if not field.get("required"):
            continue
        name = field["name"]
        value = credentials.get(name) if field.get("secret") else config.metadata.get(name)
        if value in (None, ""):
            missing.append(name)
    return missing


def _normalize_metadata(definition: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    allowed_fields = {field["name"]: field for field in definition.get("fields", []) if not field.get("secret")}
    for name, field in allowed_fields.items():
        if field.get("read_only"):
            continue
        value = payload.get(name, field.get("default"))
        if value is None:
            continue
        kind = field.get("kind")
        if kind == "boolean":
            clean[name] = bool(value)
        elif kind == "number":
            if value == "":
                continue
            try:
                clean[name] = int(value)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"metadata": {name: "Informe um número válido."}}) from exc
        else:
            clean[name] = str(value).strip()[:2000]
    if clean.get("use_tls") and clean.get("use_ssl"):
        raise ValidationError({"metadata": {"use_ssl": "TLS e SSL não podem ser ativados ao mesmo tempo."}})
    return clean


@transaction.atomic
def configure_channel(
    config: CommunicationChannelConfig,
    *,
    provider: str,
    metadata: dict[str, Any] | None = None,
    secrets: dict[str, Any] | None = None,
    sender: str = "",
    public_identifier: str = "",
    save_as_draft: bool = False,
    confirm_provider_change: bool = False,
) -> CommunicationChannelConfig:
    definition = _provider_definition(config.channel, provider)
    provider_changed = bool(config.provider and config.provider != provider)
    if provider_changed and config.is_active and not confirm_provider_change:
        raise ValidationError({"confirm_provider_change": "Confirme a troca do provedor ativo."})

    current_credentials = {} if provider_changed else config.get_credentials()
    allowed_secret_fields = set(definition.get("secret_fields", []))
    for name, value in (secrets or {}).items():
        if name not in allowed_secret_fields:
            continue
        normalized = str(value or "").strip()
        if normalized:
            current_credentials[name] = normalized

    config.provider = provider
    config.metadata = _normalize_metadata(definition, metadata or {})
    config.sender = str(sender or config.metadata.get("sender_email") or config.metadata.get("sender") or "")[:160]
    config.public_identifier = str(
        public_identifier
        or config.metadata.get("phone_number_id")
        or config.metadata.get("account_sid")
        or ""
    )[:160]
    config.set_credentials({key: value for key, value in current_credentials.items() if key in allowed_secret_fields})
    config.is_active = False if provider_changed else config.is_active
    config.last_validated_at = None
    config.last_tested_at = None
    config.clear_validation_error()

    # Uma configuração só é considerada operacional após o teste explícito.
    # Mesmo completa, ela permanece incompleta até validate_channel_configuration().
    get_missing_configuration_fields(config)
    config.connection_status = CommunicationChannelConfig.ConnectionStatus.INCOMPLETE
    config.save()
    return config


@transaction.atomic
def validate_channel_configuration(config: CommunicationChannelConfig) -> CommunicationChannelConfig:
    if get_missing_configuration_fields(config):
        config.connection_status = CommunicationChannelConfig.ConnectionStatus.INCOMPLETE
        config.last_tested_at = timezone.now()
        config.last_error_code = "IncompleteConfiguration"
        config.last_error_message = "Preencha todos os campos obrigatórios antes de testar."
        config.save(update_fields=["connection_status", "last_tested_at", "last_error_code", "last_error_message", "updated_at"])
        raise ValidationError(config.last_error_message)

    config.connection_status = CommunicationChannelConfig.ConnectionStatus.VALIDATING
    config.last_tested_at = timezone.now()
    config.clear_validation_error()
    config.save(update_fields=["connection_status", "last_tested_at", "last_error_code", "last_error_message", "updated_at"])

    provider = get_provider(config.channel, config=config)
    try:
        provider.validate_configuration(config.owner)
    except (ProviderError, ProviderNotConfigured) as exc:
        config.connection_status = CommunicationChannelConfig.ConnectionStatus.ERROR
        config.last_error_code = exc.__class__.__name__[:80]
        config.last_error_message = str(exc)[:255] or "Não foi possível validar a configuração."
        config.save(update_fields=["connection_status", "last_error_code", "last_error_message", "updated_at"])
        raise ValidationError(config.last_error_message) from exc

    now = timezone.now()
    config.connection_status = CommunicationChannelConfig.ConnectionStatus.CONFIGURED
    config.last_validated_at = now
    config.last_tested_at = now
    config.clear_validation_error()
    config.save(update_fields=["connection_status", "last_validated_at", "last_tested_at", "last_error_code", "last_error_message", "updated_at"])
    return config


@transaction.atomic
def remove_channel_configuration(config: CommunicationChannelConfig) -> CommunicationChannelConfig:
    if config.channel in {Communication.Channel.IN_APP, Communication.Channel.WHATSAPP_MANUAL}:
        raise ValidationError("Este canal nativo não pode ter a configuração removida.")

    config.is_active = False
    config.sender = ""
    config.public_identifier = ""
    config.metadata = {}
    config.set_credentials({})
    config.last_validated_at = None
    config.last_tested_at = None
    config.clear_validation_error()
    if config.channel == Communication.Channel.EMAIL:
        config.provider = "django_email"
        config.connection_status = CommunicationChannelConfig.ConnectionStatus.INCOMPLETE
    else:
        config.provider = ""
        config.connection_status = CommunicationChannelConfig.ConnectionStatus.NOT_CONFIGURED
    config.save()
    return config
