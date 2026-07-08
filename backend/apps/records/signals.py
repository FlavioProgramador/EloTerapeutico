"""
apps/records/signals.py
Signals do app de Prontuários Eletrônicos (Records).
"""

from datetime import timedelta

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Evolution


@receiver(pre_save, sender=Evolution)
def auto_lock_evolution_on_save(sender, instance, **kwargs):
    """
    Garante que se a evolução foi criada há mais de 48 horas,
    ela é bloqueada automaticamente antes de qualquer alteração ser persistida.
    """
    if instance.pk:
        # Objeto já persistido no banco
        # Verifica se já expirou o tempo de 48h
        limite = instance.created_at + timedelta(hours=48)
        if not instance.is_locked and timezone.now() >= limite:
            instance.is_locked = True
            instance.locked_at = timezone.now()
