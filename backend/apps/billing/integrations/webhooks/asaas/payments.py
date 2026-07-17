"""Alias temporário para o módulo canônico de pagamentos do webhook Asaas.

O alias em ``sys.modules`` preserva patch points históricos sem duplicar
implementação nem criar uma segunda referência independente das funções.
"""

import sys

from apps.billing.integrations.asaas.webhooks import payments as _canonical

sys.modules[__name__] = _canonical
