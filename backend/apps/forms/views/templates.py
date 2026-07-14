from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.selectors import active_form_templates
from apps.forms.serializers import FormTemplateSerializer, TherapeuticFormSerializer

from .base import FormsPagination


class FormTemplateListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FormsPagination

    def get(self, request):
        queryset = active_form_templates(params=request.query_params)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(FormTemplateSerializer(page, many=True).data)


class FormTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        template = get_object_or_404(active_form_templates(), pk=pk)
        return Response(FormTemplateSerializer(template).data)


class FormFromTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, template_id):
        template = get_object_or_404(active_form_templates(), pk=template_id)
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
