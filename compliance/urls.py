from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, ArchiveRecordViewSet


router = DefaultRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="auditlog")
router.register(r"archives", ArchiveRecordViewSet, basename="archiverecord")


urlpatterns = [
    path("", include(router.urls)),
]


