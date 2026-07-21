from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.exceptions import FinalizedSubmissionError
from apps.forms.models import FormSubmission
from apps.forms.selectors import submissions_for_form, submissions_for_user
from apps.forms.serializers import FormSubmissionSerializer
from apps.forms.services import submit_form_submission

from .base import FormsPagination, UserFormMixin


class FormSubmissionListCreateView(UserFormMixin, APIView):
    pagination_class = FormsPagination

    def get(self, request, form_id):
        form = self.get_form(form_id)
        queryset = submissions_for_form(form=form)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            FormSubmissionSerializer(
                page,
                many=True,
                context={"request": request, "form": form},
            ).data
        )

    def post(self, request, form_id):
        form = self.get_form(form_id)
        serializer = FormSubmissionSerializer(
            data=request.data,
            context={"request": request, "form": form},
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(
            FormSubmissionSerializer(
                submission,
                context={"request": request, "form": form},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class FormSubmissionDetailView(UserFormMixin, APIView):
    def get_submission(self, request, pk):
        return get_object_or_404(
            submissions_for_user(
                user=request.user,
                organization=self.get_organization(),
            ),
            pk=pk,
        )

    def get(self, request, pk):
        submission = self.get_submission(request, pk)
        return Response(
            FormSubmissionSerializer(
                submission,
                context={"request": request, "form": submission.form},
            ).data
        )

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
        return Response(
            FormSubmissionSerializer(
                submission,
                context={"request": request, "form": submission.form},
            ).data
        )


class FormSubmissionSubmitView(FormSubmissionDetailView):
    def post(self, request, pk):
        try:
            submission = submit_form_submission(
                actor=request.user,
                submission=self.get_submission(request, pk),
            )
        except FinalizedSubmissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            FormSubmissionSerializer(
                submission,
                context={"request": request, "form": submission.form},
            ).data
        )
