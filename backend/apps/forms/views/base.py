from typing import Any, cast

from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.forms.selectors import forms_for_owner


class FormsPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class UserFormMixin:
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return forms_for_owner(owner=cast(Any, self).request.user)

    def get_form(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)
