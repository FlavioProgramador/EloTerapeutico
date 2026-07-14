from django.urls import path

from apps.forms.views import (
    FormArchiveView,
    FormDetailView,
    FormDuplicateView,
    FormFromTemplateView,
    FormListCreateView,
    FormRestoreView,
    FormSubmissionDetailView,
    FormSubmissionListCreateView,
    FormSubmissionSubmitView,
    FormTemplateDetailView,
    FormTemplateListView,
)

urlpatterns = [
    path("", FormListCreateView.as_view(), name="forms-list"),
    path("<int:pk>/", FormDetailView.as_view(), name="forms-detail"),
    path("<int:pk>/duplicate/", FormDuplicateView.as_view(), name="forms-duplicate"),
    path("<int:pk>/archive/", FormArchiveView.as_view(), name="forms-archive"),
    path("<int:pk>/restore/", FormRestoreView.as_view(), name="forms-restore"),
    path(
        "<int:form_id>/submissions/",
        FormSubmissionListCreateView.as_view(),
        name="forms-submissions",
    ),
    path("templates/", FormTemplateListView.as_view(), name="form-templates"),
    path("templates/<int:pk>/", FormTemplateDetailView.as_view(), name="form-template-detail"),
    path(
        "from-template/<int:template_id>/",
        FormFromTemplateView.as_view(),
        name="forms-from-template",
    ),
    path("submissions/<int:pk>/", FormSubmissionDetailView.as_view(), name="form-submission-detail"),
    path(
        "submissions/<int:pk>/submit/",
        FormSubmissionSubmitView.as_view(),
        name="form-submission-submit",
    ),
]
