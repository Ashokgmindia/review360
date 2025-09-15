from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import AuditLog, ArchiveRecord
from .serializers import AuditLogSerializer, ArchiveRecordSerializer
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission


@extend_schema_view(
    list=extend_schema(tags=["Compliance"]),
    retrieve=extend_schema(tags=["Compliance"]),
)
class AuditLogViewSet(CollegeScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("college", "user").order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin"},
        "retrieve": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["table_name", "action"]
    search_fields = ["table_name", "action"]
    ordering_fields = ["created_at"]


@extend_schema_view(
    list=extend_schema(tags=["Compliance"]),
    retrieve=extend_schema(tags=["Compliance"]),
)
class ArchiveRecordViewSet(CollegeScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ArchiveRecord.objects.select_related("college").order_by("-archived_at")
    serializer_class = ArchiveRecordSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin"},
        "retrieve": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["table_name"]
    search_fields = ["table_name"]
    ordering_fields = ["archived_at"]


