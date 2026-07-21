from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.selectors import filtered_forms_for_user
from apps.forms.serializers import TherapeuticFormSerializer
from apps.forms.services import (
    archive_form,
    delete_or_archive_form,
    duplicate_form,
    restore_form,
)

from .base import FormsPagination, UserFormMixin


class FormListCreateView(UserFormMixin, APIView):
    pagination_class = FormsPagination

    def get(self, request):
        queryset = filtered_forms_for_user(
            user=request.user,
            organization=self.get_organization(),
            params=request.query_params,
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            TherapeuticFormSerializer(
                page,
                many=True,
                context={"request": request},
            ).data
        )

    def post(self, request):
        serializer = TherapeuticFormSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        form = serializer.save()
        return Response(
            TherapeuticFormSerializer(
                form,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class FormDetailView(UserFormMixin, APIView):
    def get(self, request, pk):
        return Response(
            TherapeuticFormSerializer(
                self.get_form(pk),
                context={"request": request},
            ).data
        )

    def patch(self, request, pk):
        form = self.get_form(pk)
        serializer = TherapeuticFormSerializer(
            form,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        form = serializer.save()
        return Response(
            TherapeuticFormSerializer(
                form,
                context={"request": request},
            ).data
        )

    def delete(self, request, pk):
        form, deleted = delete_or_archive_form(
            actor=request.user,
            organization=self.get_organization(),
            form=self.get_form(pk),
        )
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            TherapeuticFormSerializer(
                form,
                context={"request": request},
            ).data
        )


class FormArchiveView(UserFormMixin, APIView):
    def post(self, request, pk):
        form = archive_form(
            actor=request.user,
            organization=self.get_organization(),
            form=self.get_form(pk),
        )
        return Response(
            TherapeuticFormSerializer(
                form,
                context={"request": request},
            ).data
        )


class FormRestoreView(UserFormMixin, APIView):
    def post(self, request, pk):
        form = restore_form(
            actor=request.user,
            organization=self.get_organization(),
            form=self.get_form(pk),
        )
        return Response(
            TherapeuticFormSerializer(
                form,
                context={"request": request},
            ).data
        )


class FormDuplicateView(UserFormMixin, APIView):
    def post(self, request, pk):
        copy = duplicate_form(
            actor=request.user,
            organization=self.get_organization(),
            source=self.get_form(pk),
        )
        return Response(
            TherapeuticFormSerializer(
                copy,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )
