from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentLibraryViewSet,
    DocumentTemplateViewSet,
    GeneratedDocumentViewSet,
    PlaceholderListView,
)

router = DefaultRouter()
router.register("templates", DocumentTemplateViewSet, basename="document-template")
router.register("library", DocumentLibraryViewSet, basename="document-library")
router.register("generated", GeneratedDocumentViewSet, basename="generated-document")

urlpatterns = [
    path("placeholders/", PlaceholderListView.as_view(), name="document-placeholders"),
    path("", include(router.urls)),
]
