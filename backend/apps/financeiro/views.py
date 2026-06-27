"""
apps/financeiro/views.py
Views e ViewSets para o app Financeiro.
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import FinancialTransaction
from .filters import FinancialTransactionFilter
from .serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionCreateUpdateSerializer,
    MonthlySummarySerializer,
    MarkAsPaidSerializer,
)


class FinancialPermission(IsAuthenticated):
    """
    Permissão do módulo financeiro:
    - Admin e Secretária: Acesso total para gerenciar receitas e despesas.
    - Terapeuta: Acesso apenas às suas próprias transações.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_admin_role or request.user.is_therapist or request.user.is_secretary

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role or user.is_secretary:
            return True
        return obj.therapist == user


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestão de transações financeiras (receitas e despesas).
    """
    permission_classes = [FinancialPermission]
    filterset_class = FinancialTransactionFilter
    ordering_fields = ["created_at", "due_date", "amount", "payment_status"]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return FinancialTransaction.objects.none()

        # Admin e secretária veem todas as transações
        if user.is_admin_role or user.is_secretary:
            return FinancialTransaction.objects.all().select_related("patient", "appointment", "therapist")

        # Terapeutas veem apenas as suas transações
        return FinancialTransaction.objects.filter(therapist=user).select_related("patient", "appointment", "therapist")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TransactionCreateUpdateSerializer
        if self.action == "list":
            return TransactionListSerializer
        if self.action == "mark_as_paid":
            return MarkAsPaidSerializer
        return TransactionDetailSerializer

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """
        Retorna o resumo financeiro mensal para o terapeuta autenticado.
        Parâmetros de busca (query params): year (ano) e month (mês).
        GET /api/v1/financeiro/summary/?year=2026&month=6
        """
        today = timezone.localdate()
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        try:
            year = int(year) if year else today.year
            month = int(month) if month else today.month
            if not (1 <= month <= 12):
                raise ValueError()
        except ValueError:
            return Response(
                {"detail": "Ano e mês devem ser inteiros válidos, com mês de 1 a 12."},
                status=status.HTTP_400_BAD_REQUEST
            )

        therapist = request.user
        # Se for admin/secretaria e especificar therapist_id nas query params, retorna o resumo daquele terapeuta
        therapist_id = request.query_params.get("therapist_id")
        if (request.user.is_admin_role or request.user.is_secretary) and therapist_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            from django.shortcuts import get_object_or_404
            therapist = get_object_or_404(User, id=therapist_id, role="therapist")

        summary_data = FinancialTransaction.monthly_summary(therapist, year, month)
        serializer = MonthlySummarySerializer(summary_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="pay")
    def mark_as_paid(self, request, pk=None):
        """
        Marca uma transação financeira como paga, atualizando método e data de pagamento.
        PATCH /api/v1/financeiro/{id}/pay/
        """
        transaction = self.get_object()
        
        if transaction.payment_status == FinancialTransaction.PaymentStatus.PAID:
            return Response(
                {"detail": "Esta transação já foi paga anteriormente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(transaction, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Seta status como pago
        transaction.payment_status = FinancialTransaction.PaymentStatus.PAID
        transaction.paid_at = serializer.validated_data.get("paid_at")
        transaction.payment_method = serializer.validated_data.get("payment_method")
        transaction.save()

        # Atualiza a consulta associada (se houver) para status confirmado se o pagamento foi realizado
        # (normalmente a consulta já estaria confirmada, mas garante consistência)
        if transaction.appointment:
            appointment = transaction.appointment
            if appointment.status == appointment.Status.SCHEDULED:
                appointment.status = appointment.Status.CONFIRMED
                appointment.save(update_fields=["status", "updated_at"])

        detail_serializer = TransactionDetailSerializer(transaction, context={"request": request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request):
        """
        Retorna todas as transações pendentes de pagamento ordenadas pela data de vencimento.
        GET /api/v1/financeiro/pending/
        """
        qs = self.get_queryset().filter(
            payment_status=FinancialTransaction.PaymentStatus.PENDING
        )
        
        # Filtra opcionalmente por paciente
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        qs = qs.order_by("due_date", "created_at")
        
        # Paginação
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="receipt")
    def generate_receipt(self, request, pk=None):
        """
        Gera um recibo no Azure Blob Storage e retorna a URL pública.
        POST /api/v1/financeiro/{id}/receipt/
        """
        # TODO: Implementar upload de PDF gerado no Azure Blob Storage
        return Response(
            {"detail": "Geração de recibo em desenvolvimento (501 Not Implemented)."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Cancela uma transação financeira pendente.
        POST /api/v1/financeiro/{id}/cancel/
        """
        transaction = self.get_object()
        from django.core.exceptions import ValidationError
        try:
            transaction.cancel()
        except ValidationError as e:
            return Response({"detail": str(e.messages[0]) if hasattr(e, "messages") else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        detail_serializer = TransactionDetailSerializer(transaction, context={"request": request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        """
        Estorna uma transação financeira paga.
        POST /api/v1/financeiro/{id}/refund/
        """
        transaction = self.get_object()
        from django.core.exceptions import ValidationError
        try:
            transaction.refund()
        except ValidationError as e:
            return Response({"detail": str(e.messages[0]) if hasattr(e, "messages") else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        detail_serializer = TransactionDetailSerializer(transaction, context={"request": request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        """
        Exporta as transações financeiras filtradas do terapeuta logado em formato CSV.
        GET /api/v1/financeiro/export/
        """
        import csv
        from django.http import HttpResponse
        
        # Obtém o queryset filtrado usando os filtros do filterset
        queryset = self.filter_queryset(self.get_queryset())
        
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="fluxo-financeiro.csv"'
        
        writer = csv.writer(response, delimiter=";")
        # Cabeçalhos
        writer.writerow([
            "ID",
            "Tipo",
            "Categoria",
            "Valor (R$)",
            "Forma de Pagamento",
            "Status",
            "Paciente",
            "Vencimento",
            "Pago em",
            "Descrição",
            "Criado em"
        ])
        
        for tx in queryset:
            # Protege contra injeção de fórmulas CSV se o campo descrição começar com símbolos perigosos
            desc = tx.description
            if desc and desc[0] in ["=", "+", "-", "@"]:
                desc = "'" + desc
            
            patient_name = tx.patient.full_name if tx.patient else "Não associado"
            due_date = tx.due_date.strftime("%d/%m/%Y") if tx.due_date else ""
            paid_at = tx.paid_at.strftime("%d/%m/%Y %H:%M") if tx.paid_at else ""
            created_at = tx.created_at.strftime("%d/%m/%Y %H:%M")
            
            writer.writerow([
                tx.id,
                tx.get_transaction_type_display(),
                tx.get_category_display(),
                f"{tx.amount:.2f}".replace(".", ","),
                tx.get_payment_method_display(),
                tx.get_payment_status_display(),
                patient_name,
                due_date,
                paid_at,
                desc,
                created_at
            ])
            
        return response

    @action(detail=False, methods=["get"], url_path="unbilled-appointments")
    def unbilled_appointments(self, request):
        """
        Retorna as consultas concluídas ou confirmadas do terapeuta logado
        que ainda não possuem transações financeiras vinculadas.
        GET /api/v1/financeiro/unbilled-appointments/
        """
        from apps.agenda.models import Appointment
        
        user = request.user
        if user.is_anonymous:
            return Response([], status=status.HTTP_401_UNAUTHORIZED)
            
        unbilled = Appointment.objects.filter(
            therapist=user,
            status="confirmed"
        ).exclude(
            financial_transactions__isnull=False
        ).select_related("patient").order_by("-start_time")
        
        # Serialização mínima
        data = []
        for appt in unbilled:
            data.append({
                "id": appt.id,
                "patient_id": appt.patient.id,
                "patient_name": appt.patient.full_name,
                "start_time": appt.start_time,
                "end_time": appt.end_time,
                "session_value": str(appt.session_value) if appt.session_value else "0.00"
            })
            
        return Response(data, status=status.HTTP_200_OK)
