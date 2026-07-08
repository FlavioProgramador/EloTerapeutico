"""Actions de geração idempotente de cobranças por sessão."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.agenda.models import Appointment

from ...models import FinancialTransaction


class BillingActions:
    @action(detail=False, methods=["post"], url_path="generate-monthly-charges")
    def generate_monthly_charges(self, request):
        appointment_ids = request.data.get("appointment_ids") or []
        try:
            due_date = date.fromisoformat(request.data.get("due_date"))
            appointment_ids = [int(value) for value in appointment_ids]
            if not appointment_ids or len(appointment_ids) != len(set(appointment_ids)):
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"detail": "Selecione sessões válidas e informe o vencimento."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                appointments = list(
                    Appointment.objects.select_for_update()
                    .filter(
                        id__in=appointment_ids,
                        therapist=request.user,
                        status__in=[Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED],
                    )
                    .select_related("patient")
                    .order_by("id")
                )
                if len(appointments) != len(appointment_ids):
                    raise ValidationError(
                        "Uma ou mais sessões não pertencem ao profissional ou não são elegíveis."
                    )

                created = []
                skipped = []
                for appointment in appointments:
                    already_billed = FinancialTransaction.objects.filter(
                        appointment=appointment
                    ).exclude(payment_status=FinancialTransaction.PaymentStatus.CANCELLED)
                    if already_billed.exists():
                        skipped.append(appointment.pk)
                        continue
                    if not appointment.session_value or appointment.session_value <= 0:
                        raise ValidationError(
                            f"A sessão {appointment.pk} não possui valor configurado."
                        )
                    charge = FinancialTransaction.objects.create(
                        therapist=request.user,
                        patient=appointment.patient,
                        appointment=appointment,
                        transaction_type=FinancialTransaction.TransactionType.INCOME,
                        category=FinancialTransaction.Category.SESSION,
                        source=FinancialTransaction.Source.APPOINTMENT,
                        amount=appointment.session_value,
                        due_date=due_date,
                        description=f"Sessão de {appointment.start_time:%d/%m/%Y}",
                    )
                    created.append(charge.pk)
        except ValidationError as exc:
            return Response(
                {"detail": exc.messages[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"created": created, "skipped": skipped, "created_count": len(created)},
            status=status.HTTP_201_CREATED,
        )
