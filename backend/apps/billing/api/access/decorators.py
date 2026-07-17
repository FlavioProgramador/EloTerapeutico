from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.billing.services.features import can_use_feature


def require_feature(feature_key: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not can_use_feature(request.user, feature_key):
                raise PermissionDenied(
                    "Seu plano atual não possui acesso a este recurso."
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
