from typing import Any, cast

from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission

from apps.forms.selectors import forms_for_user
from apps.organizations.permissions import has_capability
from apps.organizations.services.tenant_context import ensure_request_organization


class FormsPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        _, membership = ensure_request_organization(request=request, required=True)
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return has_capability(membership, "forms.view")
        return has_capability(membership, "forms.manage")


class FormsPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class UserFormMixin:
    permission_classes = [FormsPermission]

    def get_organization(self):
        organization, _ = ensure_request_organization(
            request=cast(Any, self).request,
            required=True,
        )
        return organization

    def get_queryset(self):
        request = cast(Any, self).request
        return forms_for_user(
            user=request.user,
            organization=self.get_organization(),
        )

    def get_form(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)
