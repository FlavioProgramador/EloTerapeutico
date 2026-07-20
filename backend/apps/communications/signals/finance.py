from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.communications.services import (
    cancel_pending_for_source,
    emit_domain_event,
)
from apps.finances.models import FinancialTransaction

from .common import capture_previous


@receiver(pre_save, sender=FinancialTransaction)
def capture_financial_previous_state(sender, instance, **kwargs):
    capture_previous(
        sender,
        instance,
        ("payment_status", "due_date", "updated_at"),
        "_communications_previous_state",
    )


@receiver(post_save, sender=FinancialTransaction)
def enqueue_financial_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)
    if (
        instance.patient_id is None
        or instance.transaction_type
        != FinancialTransaction.TransactionType.INCOME
    ):
        return

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        amount = Decimal(str(instance.amount))
        variables = {
            "payment_amount": f"R$ {amount:.2f}",
            "payment_due_date": (
                instance.due_date.strftime("%d/%m/%Y")
                if instance.due_date
                else ""
            ),
            "payment_status": instance.get_payment_status_display(),
        }
        if created:
            emit_domain_event(
                owner=instance.therapist,
                event_type="financial.payment_created",
                patient=instance.patient,
                financial_transaction=instance,
                source_object_type=FinancialTransaction._meta.label,
                source_object_id=source_id,
                variables=variables,
                event_version=version,
            )
        if previous and previous["payment_status"] != instance.payment_status:
            if instance.payment_status == FinancialTransaction.PaymentStatus.PAID:
                cancel_pending_for_source(
                    owner=instance.therapist,
                    source_event_prefix="financial.",
                    source_object_type=FinancialTransaction._meta.label,
                    source_object_id=source_id,
                )
                emit_domain_event(
                    owner=instance.therapist,
                    event_type="financial.payment_confirmed",
                    patient=instance.patient,
                    financial_transaction=instance,
                    source_object_type=FinancialTransaction._meta.label,
                    source_object_id=source_id,
                    variables=variables,
                    event_version=version,
                )
            elif instance.payment_status in {
                FinancialTransaction.PaymentStatus.CANCELLED,
                FinancialTransaction.PaymentStatus.REFUNDED,
            }:
                cancel_pending_for_source(
                    owner=instance.therapist,
                    source_event_prefix="financial.",
                    source_object_type=FinancialTransaction._meta.label,
                    source_object_id=source_id,
                )

    transaction.on_commit(dispatch_event)
