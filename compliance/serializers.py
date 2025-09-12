from rest_framework import serializers
from .models import AuditLog, ArchiveRecord


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "table_name", "record_id", "action", "details", "created_at"]
        read_only_fields = ["id", "created_at"]


class ArchiveRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchiveRecord
        fields = ["id", "table_name", "original_id", "archived_at", "payload"]
        read_only_fields = ["id", "archived_at"]


