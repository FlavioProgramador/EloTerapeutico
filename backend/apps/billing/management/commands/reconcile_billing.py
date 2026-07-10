from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.billing.models import BillingOrder, Subscription
from apps.billing.services.access import SubscriptionAccessService
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.orders import get_gateway, sync_installment_payments, sync_subscription_payments


class Command(BaseCommand):
    help = "Reconcilia assinaturas, parcelamentos e períodos de acesso com o gateway."

    def add_arguments(self, parser):
        parser.add_argument("--order", dest="order_public_id", help="UUID público de uma contratação específica.")

    def handle(self, *args, **options):
        gateway = get_gateway()
        queryset = BillingOrder.objects.select_related("plan", "plan_price", "user").filter(
            status__in=[
                BillingOrder.Status.PENDING,
                BillingOrder.Status.PARTIALLY_PAID,
                BillingOrder.Status.PAID,
                BillingOrder.Status.OVERDUE,
            ]
        )
        if options.get("order_public_id"):
            queryset = queryset.filter(public_id=options["order_public_id"])

        synchronized = 0
        failed = 0
        previous_subscriptions_canceled = 0
        for order in queryset.iterator():
            try:
                if order.gateway_installment_id:
                    sync_installment_payments(order, gateway=gateway)
                elif order.gateway_subscription_id:
                    sync_subscription_payments(order, gateway=gateway)

                metadata = dict(order.metadata or {})
                previous_id = metadata.get("previous_gateway_subscription_id")
                if metadata.get("previous_subscription_cancel_pending") and previous_id:
                    if previous_id != order.gateway_subscription_id:
                        gateway.cancel_subscription(previous_id)
                    metadata["previous_subscription_cancel_pending"] = False
                    metadata["previous_subscription_canceled_at"] = timezone.now().isoformat()
                    order.metadata = metadata
                    order.save(update_fields=["metadata", "updated_at"])
                    previous_subscriptions_canceled += 1
                synchronized += 1
            except GatewayError as exc:
                failed += 1
                self.stderr.write(f"Falha ao sincronizar {order.public_id}: {exc}")

        suspended = 0
        for subscription in Subscription.objects.filter(status=Subscription.Status.PAST_DUE).iterator():
            before = subscription.status
            updated = SubscriptionAccessService.suspend_if_grace_expired(subscription)
            if before != updated.status:
                suspended += 1

        expired = 0
        expiring = Subscription.objects.filter(
            cancel_at_period_end=True,
            access_ends_at__lt=timezone.now(),
            status__in=[Subscription.Status.ACTIVE, Subscription.Status.PAST_DUE],
        )
        for subscription in expiring.iterator():
            try:
                if subscription.gateway_subscription_id:
                    gateway.cancel_subscription(subscription.gateway_subscription_id)
            except GatewayError as exc:
                failed += 1
                self.stderr.write(f"Falha ao cancelar assinatura {subscription.pk} no gateway: {exc}")
                continue
            with transaction.atomic():
                locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
                locked.status = Subscription.Status.CANCELED
                locked.canceled_at = timezone.now()
                locked.cancel_at_period_end = False
                locked.save(update_fields=["status", "canceled_at", "cancel_at_period_end", "updated_at"])
                expired += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliação concluída: {synchronized} contratos, {failed} falhas, "
                f"{suspended} suspensões, {expired} cancelamentos efetivados e "
                f"{previous_subscriptions_canceled} recorrências anteriores encerradas."
            )
        )
