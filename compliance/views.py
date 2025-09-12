from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditLog, ArchiveRecord
from .serializers import AuditLogSerializer, ArchiveRecordSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["table_name", "action"]
    search_fields = ["table_name", "action"]
    ordering_fields = ["created_at"]


class ArchiveRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ArchiveRecord.objects.all().order_by("-archived_at")
    serializer_class = ArchiveRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["table_name"]
    search_fields = ["table_name"]
    ordering_fields = ["archived_at"]


