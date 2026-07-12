# mypy: ignore-errors
from __future__ import annotations

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.api.serializers.forms_serializers import (
    FormSubmissionSerializer,
    FormTemplateSerializer,
    TherapeuticFormSerializer,
)
from apps.forms.models import FormField, FormSubmission, FormTemplate, TherapeuticForm


class FormsPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class UserFormMixin:
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            TherapeuticForm.objects.filter(owner=self.request.user)
            .select_related("created_by", "updated_by", "source_template")
            .prefetch_related("fields")
            .annotate(submissions_total=Count("submissions"))
        )

    def get_form(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)


class FormListCreateView(UserFormMixin, APIView):
    pagination_class = FormsPagination

    def get(self, request):
        queryset = self.get_queryset()
        search = request.query_params.get("search", "").strip()
        status_filter = request.query_params.get("status", "").strip()
        category = request.query_params.get("category", "").strip()
        ordering = request.query_params.get("ordering", "-updated_at")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search) | Q(category__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category:
            queryset = queryset.filter(category=category)
        if ordering in {"name", "-name", "created_at", "-created_at", "updated_at", "-updated_at"}:
            queryset = queryset.order_by(ordering)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(TherapeuticFormSerializer(page, many=True).data)

    def post(self, request):
        serializer = TherapeuticFormSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        form = serializer.save()
        return Response(TherapeuticFormSerializer(form).data, status=status.HTTP_201_CREATED)


class FormDetailView(UserFormMixin, APIView):
    def get(self, request, pk):
        return Response(TherapeuticFormSerializer(self.get_form(pk)).data)

    def patch(self, request, pk):
        form = self.get_form(pk)
        serializer = TherapeuticFormSerializer(form, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        form = serializer.save()
        return Response(TherapeuticFormSerializer(form).data)

    def delete(self, request, pk):
        form = self.get_form(pk)
        if form.submissions.exists():
            form.archive(request.user)
            return Response(TherapeuticFormSerializer(form).data)
        form.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FormArchiveView(UserFormMixin, APIView):
    def post(self, request, pk):
        form = self.get_form(pk)
        form.archive(request.user)
        return Response(TherapeuticFormSerializer(form).data)


class FormRestoreView(UserFormMixin, APIView):
    def post(self, request, pk):
        form = self.get_form(pk)
        form.restore(request.user)
        return Response(TherapeuticFormSerializer(form).data)


class FormDuplicateView(UserFormMixin, APIView):
    @transaction.atomic
    def post(self, request, pk):
        source = self.get_form(pk)
        copy = TherapeuticForm.objects.create(
            owner=request.user,
            name=f"{source.name} (cópia)",
            description=source.description,
            category=source.category,
            source_template=source.source_template,
            created_by=request.user,
            updated_by=request.user,
        )
        FormField.objects.bulk_create(
            [
                FormField(
                    form=copy,
                    type=field.type,
                    label=field.label,
                    placeholder=field.placeholder,
                    help_text=field.help_text,
                    required=field.required,
                    order=field.order,
                    is_visible=field.is_visible,
                    internal_id=field.internal_id,
                    config=field.config,
                )
                for field in source.fields.all()
            ]
        )
        return Response(TherapeuticFormSerializer(copy).data, status=status.HTTP_201_CREATED)


class FormTemplateListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FormsPagination

    def get(self, request):
        queryset = FormTemplate.objects.filter(is_active=True)
        search = request.query_params.get("search", "").strip()
        category = request.query_params.get("category", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search) | Q(category__icontains=search)
            )
        if category:
            queryset = queryset.filter(category=category)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(FormTemplateSerializer(page, many=True).data)


class FormTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        template = get_object_or_404(FormTemplate, pk=pk, is_active=True)
        return Response(FormTemplateSerializer(template).data)


class FormFromTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, template_id):
        template = get_object_or_404(FormTemplate, pk=template_id, is_active=True)
        payload = {
            "name": request.data.get("name") or template.name,
            "description": request.data.get("description") or template.description,
            "category": request.data.get("category") or template.category,
            "fields": request.data.get("fields") or template.fields_schema,
        }
        serializer = TherapeuticFormSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        form = serializer.save(source_template=template)
        return Response(TherapeuticFormSerializer(form).data, status=status.HTTP_201_CREATED)


class FormSubmissionListCreateView(UserFormMixin, APIView):
    pagination_class = FormsPagination

    def get(self, request, form_id):
        form = self.get_form(form_id)
        queryset = form.submissions.select_related("patient", "professional", "submitted_by").prefetch_related(
            "answers", "answers__field"
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(FormSubmissionSerializer(page, many=True).data)

    def post(self, request, form_id):
        form = self.get_form(form_id)
        serializer = FormSubmissionSerializer(data=request.data, context={"request": request, "form": form})
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(FormSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class FormSubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_submission(self, request, pk):
        return get_object_or_404(
            FormSubmission.objects.select_related("form", "patient", "professional").prefetch_related(
                "answers", "answers__field"
            ),
            pk=pk,
            owner=request.user,
        )

    def get(self, request, pk):
        return Response(FormSubmissionSerializer(self.get_submission(request, pk)).data)

    def patch(self, request, pk):
        submission = self.get_submission(request, pk)
        if submission.status != FormSubmission.Status.DRAFT:
            return Response(
                {"detail": "Somente rascunhos podem ser alterados."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FormSubmissionSerializer(
            submission,
            data=request.data,
            partial=True,
            context={"request": request, "form": submission.form},
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(FormSubmissionSerializer(submission).data)


class FormSubmissionSubmitView(FormSubmissionDetailView):
    def post(self, request, pk):
        submission = self.get_submission(request, pk)
        if submission.status != FormSubmission.Status.DRAFT:
            return Response({"detail": "Este formulário já foi finalizado."}, status=status.HTTP_400_BAD_REQUEST)
        submission.submit(request.user)
        return Response(FormSubmissionSerializer(submission).data)
